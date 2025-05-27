import React, { useEffect, useRef } from 'react';
import styles from './MessageList.module.css';
import MessageItem from '../MessageItem/MessageItem';
import type { Message } from '../ChatPage/ChatPage'; // Use type-only import

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className={styles.messageList}>
      {messages.map((msg) => (
        <MessageItem key={msg.id} text={msg.text} sender={msg.sender} />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
