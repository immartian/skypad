import React, { useState, useEffect, useMemo } from 'react';
import styles from './ChatPage.module.css';
import StatusIndicator from '../StatusIndicator/StatusIndicator';
import MessageList from '../MessageList/MessageList';
import MessageInput from '../MessageInput/MessageInput';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bella';
}

const BELLA_EMOJI = '🧘‍♀️'; // Or any other emoji/icon

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<string>('Online');

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        { id: 'init-bella', text: "Hi! I'm Bella. How can I help you today?", sender: 'bella' }
      ]);
    }
  }, []); // Removed messages from dependency array to avoid re-triggering

  const handleSendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setStatus('Bella is thinking...');

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        let errorDetail = 'Network response was not ok.';
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorDetail;
        } catch (jsonError) {
          errorDetail = response.statusText || errorDetail;
        }
        throw new Error(errorDetail);
      }

      const data = await response.json();
      const bellaMessage: Message = {
        id: Date.now().toString() + '-bella',
        text: data.reply,
        sender: 'bella',
      };

      setMessages((prevMessages) => [...prevMessages, bellaMessage]);
      setStatus('Online');
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessageText = error instanceof Error ? error.message : 'Sorry, I had trouble responding. Please try again.';
      const errorMessage: Message = {
        id: Date.now().toString() + '-error',
        text: errorMessageText,
        sender: 'bella',
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
      setStatus('Error communicating with Bella');
    }
  };

  const { oldMessages, recentMessages } = useMemo(() => {
    const RECENT_COUNT = 2;
    if (messages.length <= RECENT_COUNT) {
      return { oldMessages: [], recentMessages: messages };
    }
    return {
      oldMessages: messages.slice(0, messages.length - RECENT_COUNT),
      recentMessages: messages.slice(messages.length - RECENT_COUNT),
    };
  }, [messages]);

  return (
    <div className={styles.chatPage}>
      <div className={styles.oldMessagesArea}>
        <MessageList messages={oldMessages} isOldMessages={true} />
      </div>

      <div className={styles.bellaZone}>
        <div className={styles.bellaAvatar}>{BELLA_EMOJI}</div>
        <StatusIndicator status={status} />
      </div>

      <div className={styles.currentInteractionArea}>
        <MessageList messages={recentMessages} />
        <MessageInput onSendMessage={handleSendMessage} />
      </div>
    </div>
  );
};

export default ChatPage;
