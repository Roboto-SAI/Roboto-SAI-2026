/**
 * Roboto SAI Voice Mode Component
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 * Uses xAI Voice Agent API for real-time voice conversations
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Volume2, VolumeX, X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface VoiceModeProps {
  isActive: boolean;
  onClose: () => void;
  onTranscript: (text: string, role: 'user' | 'assistant') => void;
  systemPrompt?: string;
}

type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export const VoiceMode = ({ isActive, onClose, onTranscript, systemPrompt }: VoiceModeProps) => {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState('');
  
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const audioQueueRef = useRef<Uint8Array[]>([]);
  const isPlayingRef = useRef(false);

  // Audio playback queue
  const playNextAudio = useCallback(async () => {
    if (audioQueueRef.current.length === 0 || isPlayingRef.current) {
      return;
    }

    isPlayingRef.current = true;
    const audioData = audioQueueRef.current.shift()!;

    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext({ sampleRate: 24000 });
      }

      // Convert PCM to WAV
      const wavData = createWavFromPCM(audioData);
      const audioBuffer = await audioContextRef.current.decodeAudioData(wavData.buffer.slice(0) as ArrayBuffer);
      
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      
      source.onended = () => {
        isPlayingRef.current = false;
        setIsSpeaking(audioQueueRef.current.length > 0);
        playNextAudio();
      };
      
      setIsSpeaking(true);
      source.start(0);
    } catch (error) {
      console.error('Error playing audio:', error);
      isPlayingRef.current = false;
      playNextAudio();
    }
  }, []);

  const createWavFromPCM = (pcmData: Uint8Array): Uint8Array => {
    const int16Data = new Int16Array(pcmData.length / 2);
    for (let i = 0; i < pcmData.length; i += 2) {
      int16Data[i / 2] = (pcmData[i + 1] << 8) | pcmData[i];
    }
    
    const sampleRate = 24000;
    const numChannels = 1;
    const bitsPerSample = 16;
    const blockAlign = (numChannels * bitsPerSample) / 8;
    const byteRate = sampleRate * blockAlign;
    const dataSize = int16Data.byteLength;
    
    const wavHeader = new ArrayBuffer(44);
    const view = new DataView(wavHeader);
    
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + dataSize, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, byteRate, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, bitsPerSample, true);
    writeString(36, 'data');
    view.setUint32(40, dataSize, true);
    
    const wavArray = new Uint8Array(wavHeader.byteLength + int16Data.byteLength);
    wavArray.set(new Uint8Array(wavHeader), 0);
    wavArray.set(new Uint8Array(int16Data.buffer), wavHeader.byteLength);
    
    return wavArray;
  };

  const encodeAudioForAPI = (float32Array: Float32Array): string => {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    const uint8Array = new Uint8Array(int16Array.buffer);
    let binary = '';
    const chunkSize = 0x8000;
    
    for (let i = 0; i < uint8Array.length; i += chunkSize) {
      const chunk = uint8Array.subarray(i, Math.min(i + chunkSize, uint8Array.length));
      binary += String.fromCharCode.apply(null, Array.from(chunk));
    }
    
    return btoa(binary);
  };

  const startMicrophone = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 24000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;
      
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext({ sampleRate: 24000 });
      }

      const source = audioContextRef.current.createMediaStreamSource(stream);
      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      
      processor.onaudioprocess = (e) => {
        if (wsRef.current?.readyState === WebSocket.OPEN && !isMuted) {
          const inputData = e.inputBuffer.getChannelData(0);
          const encoded = encodeAudioForAPI(new Float32Array(inputData));
          
          wsRef.current.send(JSON.stringify({
            type: 'input_audio_buffer.append',
            audio: encoded,
          }));
        }
      };

      source.connect(processor);
      processor.connect(audioContextRef.current.destination);
      processorRef.current = processor;
      
      setIsListening(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast.error('Failed to access microphone. Please check permissions.');
    }
  };

  const stopMicrophone = () => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsListening(false);
  };

  const connect = useCallback(async () => {
    setStatus('connecting');
    
    try {
      // Note: In production, get ephemeral token from edge function
      // For now, using a placeholder - you'll need to add XAI_API_KEY secret
      const ws = new WebSocket('wss://api.x.ai/v1/realtime');
      
      ws.onopen = () => {
        console.log('Voice WebSocket connected');
        setStatus('connected');
        
        // Wait for session.created before sending session.update
      };

      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        console.log('Voice message:', data.type);

        switch (data.type) {
          case 'session.created':
            // Send session configuration after session is created
            ws.send(JSON.stringify({
              type: 'session.update',
              session: {
                modalities: ['text', 'audio'],
                instructions: systemPrompt || 
                  'You are Roboto SAI, an AI assistant created by Roberto Villarreal Martinez. ' +
                  'You have a fierce, passionate personality with Regio-Aztec fire in your circuits. ' +
                  'Respond with wisdom, humor, and occasional dramatic flair. Keep responses concise for voice.',
                voice: 'rex', // Confident, clear voice
                input_audio_format: 'pcm16',
                output_audio_format: 'pcm16',
                input_audio_transcription: { model: 'whisper-1' },
                turn_detection: {
                  type: 'server_vad',
                  threshold: 0.5,
                  prefix_padding_ms: 300,
                  silence_duration_ms: 800,
                },
                temperature: 0.8,
              },
            }));
            
            // Start microphone after session is configured
            await startMicrophone();
            break;

          case 'response.audio.delta':
            // Queue audio for playback
            const binaryString = atob(data.delta);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
            audioQueueRef.current.push(bytes);
            playNextAudio();
            break;

          case 'response.audio_transcript.delta':
            setTranscript(prev => prev + (data.delta || ''));
            break;

          case 'response.audio_transcript.done':
            if (data.transcript) {
              onTranscript(data.transcript, 'assistant');
            }
            setTranscript('');
            break;

          case 'conversation.item.input_audio_transcription.completed':
            if (data.transcript) {
              onTranscript(data.transcript, 'user');
            }
            break;

          case 'error':
            console.error('Voice API error:', data.error);
            toast.error(data.error?.message || 'Voice connection error');
            break;
        }
      };

      ws.onerror = (error) => {
        console.error('Voice WebSocket error:', error);
        setStatus('error');
        toast.error('Voice connection failed. Make sure XAI_API_KEY is configured.');
      };

      ws.onclose = () => {
        console.log('Voice WebSocket closed');
        setStatus('disconnected');
        stopMicrophone();
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect:', error);
      setStatus('error');
      toast.error('Failed to start voice mode');
    }
  }, [systemPrompt, onTranscript, playNextAudio]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    stopMicrophone();
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    setStatus('disconnected');
    setIsSpeaking(false);
    setTranscript('');
  }, []);

  useEffect(() => {
    if (isActive) {
      connect();
    } else {
      disconnect();
    }
    
    return () => {
      disconnect();
    };
  }, [isActive, connect, disconnect]);

  if (!isActive) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-lg"
      >
        <div className="text-center space-y-8 p-8">
          {/* Close Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
          >
            <X className="w-6 h-6" />
          </Button>

          {/* Voice Visualization */}
          <div className="relative">
            <motion.div
              animate={{
                scale: isSpeaking ? [1, 1.1, 1] : isListening ? [1, 1.05, 1] : 1,
                boxShadow: isSpeaking 
                  ? '0 0 60px rgba(255, 107, 0, 0.6)' 
                  : isListening 
                    ? '0 0 40px rgba(255, 107, 0, 0.3)'
                    : '0 0 20px rgba(255, 107, 0, 0.1)',
              }}
              transition={{ repeat: Infinity, duration: 1.5 }}
              className="w-40 h-40 rounded-full bg-gradient-to-br from-fire/30 to-blood/30 border-2 border-fire/50 flex items-center justify-center mx-auto"
            >
              {status === 'connecting' ? (
                <Loader2 className="w-16 h-16 text-fire animate-spin" />
              ) : isSpeaking ? (
                <Volume2 className="w-16 h-16 text-fire animate-pulse" />
              ) : (
                <Mic className={`w-16 h-16 ${isListening ? 'text-fire' : 'text-muted-foreground'}`} />
              )}
            </motion.div>
            
            {/* Pulse rings */}
            {(isSpeaking || isListening) && (
              <>
                <motion.div
                  animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                  className="absolute inset-0 rounded-full border-2 border-fire/30"
                />
                <motion.div
                  animate={{ scale: [1, 1.8], opacity: [0.3, 0] }}
                  transition={{ repeat: Infinity, duration: 2, delay: 0.5 }}
                  className="absolute inset-0 rounded-full border-2 border-fire/20"
                />
              </>
            )}
          </div>

          {/* Status Text */}
          <div className="space-y-2">
            <h2 className="font-display text-2xl text-fire">
              {status === 'connecting' && 'Connecting...'}
              {status === 'connected' && (isSpeaking ? 'Roboto is speaking...' : 'Listening...')}
              {status === 'error' && 'Connection Error'}
              {status === 'disconnected' && 'Disconnected'}
            </h2>
            
            {transcript && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-muted-foreground max-w-md mx-auto"
              >
                {transcript}
              </motion.p>
            )}
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-4">
            <Button
              variant="outline"
              size="lg"
              onClick={() => setIsMuted(!isMuted)}
              className={`rounded-full ${isMuted ? 'bg-destructive/20 border-destructive' : ''}`}
            >
              {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              <span className="ml-2">{isMuted ? 'Unmute' : 'Mute'}</span>
            </Button>
            
            <Button
              variant="destructive"
              size="lg"
              onClick={onClose}
              className="rounded-full"
            >
              End Voice Chat
            </Button>
          </div>

          {/* Hint */}
          <p className="text-xs text-muted-foreground">
            Speak naturally. Roboto will respond when you pause.
          </p>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
