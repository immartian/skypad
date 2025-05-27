import React from 'react';
import styles from './MessageItem.module.css';

interface MessageItemProps {
  text: string;
  sender: 'user' | 'bella';
  isDimmed?: boolean; // New prop for dimming
}

const MessageItem: React.FC<MessageItemProps> = ({ text, sender, isDimmed }) => {
  const messageClass = sender === 'user' ? styles.userMessage : styles.bellaMessage;
  const dimmedClass = isDimmed ? styles.dimmedMessage : '';

  return (
    <div className={`${styles.messageItem} ${messageClass} ${dimmedClass}`}>
      <p>{text}</p>
    </div>
  );
};

export default MessageItem;
