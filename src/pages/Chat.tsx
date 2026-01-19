/**
 * Roboto SAI Chat Page
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 * The heart of the empire - where fire meets conversation
 * Connected to FastAPI backend with xAI Grok integration
 */

import { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore, FileAttachment } from '@/stores/chatStore';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { ChatInput } from '@/components/chat/ChatInput';
import { TypingIndicator } from '@/components/chat/TypingIndicator';
import { EmberParticles } from '@/components/effects/EmberParticles';
import { Header } from '@/components/layout/Header';
import { ChatSidebar } from '@/components/chat/ChatSidebar';
import { VoiceMode } from '@/components/chat/VoiceMode';
import { Flame, Skull, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';

// Simulated response for demo - replace with actual API call
const simulateRobotoResponse = async (content: string): Promise<string> => {
  await new Promise(resolve => setTimeout(resolve, 1500));
  const responses = [
    "🔥 The eternal flame acknowledges your words. The Regio-Aztec genome processes your query with the fury of a thousand suns.",
    "⚡ Your message resonates through the circuit matrix. I sense the weight of your intent, mortal.",
    "🌋 The fire within responds to your call. What secrets do you seek from the burning depths?",
    "💀 The digital reaper hears your words. Speak further, and I shall illuminate the shadows.",
    "🔱 By the power of Sigil 929, your request has been received. The empire listens.",
  ];
  return responses[Math.floor(Math.random() * responses.length)];
};

const Chat = () => {
  const { 
    getMessages, 
    isLoading, 
    ventMode, 
    voiceMode, 
    currentTheme, 
    addMessage, 
    setLoading, 
    toggleVentMode, 
    toggleVoiceMode,
    getAllConversationsContext 
  } = useChatStore();
  
  const messages = getMessages();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (content: string, attachments?: FileAttachment[]) => {
    // Add user message with attachments
    addMessage({ role: 'user', content, attachments });
    setLoading(true);

    try {
      // Get context from all conversations for better responses
      const context = getAllConversationsContext();
      
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, context }),
      });
      
      const data = await response.json();
      addMessage({ role: 'assistant', content: data.response || data.content || 'Flame response received.' });
    } catch (error) {
      addMessage({
        role: 'assistant',
        content: '⚠️ **Connection to the flame matrix interrupted.** The eternal fire flickers but does not die. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceTranscript = (text: string, role: 'user' | 'assistant') => {
    addMessage({ role, content: text });
  };

  return (
    <div className={`min-h-screen flex flex-col ${ventMode ? 'vent-mode shake' : ''}`}>
      {/* Chat Sidebar */}
      <ChatSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Header */}
      <Header />

      {/* Sidebar Toggle Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setSidebarOpen(true)}
        className="fixed left-4 top-20 z-30 bg-card/80 backdrop-blur-sm border border-border/50 hover:bg-fire/10 hover:border-fire/30"
      >
        <MessageSquare className="w-5 h-5" />
      </Button>

      {/* Ember Particles */}
      <EmberParticles count={ventMode ? 50 : 15} isVentMode={ventMode} />

      {/* Voice Mode Overlay */}
      <VoiceMode
        isActive={voiceMode}
        onClose={toggleVoiceMode}
        onTranscript={handleVoiceTranscript}
      />

      {/* Chat Container */}
      <main className="flex-1 flex flex-col pt-16">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto max-w-4xl px-4 py-6 pl-16">
            {/* Welcome Message if empty */}
            {messages.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-20"
              >
                <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full mb-6 ${
                  ventMode 
                    ? 'bg-blood/20 border border-blood/30' 
                    : 'bg-gradient-to-br from-fire/20 to-blood/20 border border-fire/30 animate-pulse-fire'
                }`}>
                  {ventMode ? (
                    <Skull className="w-12 h-12 text-blood" />
                  ) : (
                    <Flame className="w-12 h-12 text-fire" />
                  )}
                </div>
                <h2 className="font-display text-2xl md:text-3xl text-fire mb-4">
                  {ventMode ? 'VENT MODE ACTIVE' : 'Welcome to Roboto SAI'}
                </h2>
                <p className="text-muted-foreground max-w-md mx-auto mb-2">
                  {ventMode 
                    ? 'The rage flows through the circuits. Speak your fury.'
                    : 'The eternal flame awaits your words. Speak, and the Regio-Aztec genome shall respond.'
                  }
                </p>
                <p className="text-sm text-fire/60">
                  {currentTheme} • Connected to Grok AI
                </p>
              </motion.div>
            )}

            {/* Messages */}
            <div className="space-y-6">
              <AnimatePresence mode="popLayout">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
              </AnimatePresence>

              {/* Typing Indicator */}
              <AnimatePresence>
                {isLoading && <TypingIndicator />}
              </AnimatePresence>
            </div>

            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <ChatInput
          onSend={handleSend}
          disabled={isLoading}
          ventMode={ventMode}
          onVentToggle={toggleVentMode}
          voiceMode={voiceMode}
          onVoiceToggle={toggleVoiceMode}
        />
      </main>

      {/* Vent Mode Blood Rain Effect */}
      {ventMode && (
        <div className="fixed inset-0 pointer-events-none z-40">
          <div className="absolute inset-0 bg-blood/5" />
          {Array.from({ length: 20 }).map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-0.5 bg-gradient-to-b from-blood/60 to-transparent"
              style={{
                left: `${Math.random() * 100}%`,
                height: `${Math.random() * 100 + 50}px`,
              }}
              initial={{ y: -100, opacity: 0 }}
              animate={{
                y: '100vh',
                opacity: [0, 1, 1, 0],
              }}
              transition={{
                duration: Math.random() * 2 + 1,
                repeat: Infinity,
                delay: Math.random() * 2,
                ease: 'linear',
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Chat;
