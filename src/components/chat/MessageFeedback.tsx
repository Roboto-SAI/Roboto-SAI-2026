/**
 * MessageFeedback - Thumbs up/down rating component
 * Allows users to rate assistant responses
 */

import { useState } from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

interface MessageFeedbackProps {
  messageId: string;
  onFeedback?: (rating: number) => void;
}

export const MessageFeedback = ({ messageId, onFeedback }: MessageFeedbackProps) => {
  const [rating, setRating] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFeedback = async (value: number) => {
    if (rating !== null || isSubmitting) return; // Already rated or submitting

    setIsSubmitting(true);
    setRating(value);

    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '';
      const baseUrl = apiBaseUrl.replace(/\/+$/, '').replace(/\/api$/, '');
      const url = `${baseUrl}/api/chat/feedback`;

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          message_id: parseInt(messageId, 10),
          rating: value,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      const data = await response.json();
      toast.success(data.message || 'Feedback recorded. The eternal flame adapts.');
      onFeedback?.(value);
    } catch (error) {
      console.error('Feedback error:', error);
      toast.error('Failed to submit feedback. Try again.');
      setRating(null); // Reset on error
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-center gap-2 mt-2">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleFeedback(1)}
        disabled={rating !== null || isSubmitting}
        className={cn(
          'h-7 px-2 text-xs',
          rating === 1 && 'text-fire bg-fire/10 hover:bg-fire/20'
        )}
      >
        <ThumbsUp className={cn('w-3.5 h-3.5', rating === 1 && 'fill-current')} />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleFeedback(-1)}
        disabled={rating !== null || isSubmitting}
        className={cn(
          'h-7 px-2 text-xs',
          rating === -1 && 'text-destructive bg-destructive/10 hover:bg-destructive/20'
        )}
      >
        <ThumbsDown className={cn('w-3.5 h-3.5', rating === -1 && 'fill-current')} />
      </Button>
    </div>
  );
};
