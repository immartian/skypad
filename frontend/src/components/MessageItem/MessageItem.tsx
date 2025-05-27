import React from 'react';
import styles from './MessageItem.module.css';

interface MessageItemProps {
  text: string;
  sender: 'user' | 'bella';
}

const MessageItem: React.FC<MessageItemProps> = ({ text, sender }) => {
  const messageClass = sender === 'user' ? styles.userMessage : styles.bellaMessage;
  return (
    <div className={`${styles.messageItem} ${messageClass}`}>
      <p>{text}</p>
    </div>
  );
};

export default MessageItem;
