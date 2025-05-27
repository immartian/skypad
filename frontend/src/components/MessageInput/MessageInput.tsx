import React, { useState } from 'react';
import styles from './MessageInput.module.css';

interface MessageInputProps {
  onSendMessage: (text: string) => void;
}

const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() === '') return;
    onSendMessage(message);
    setMessage('');
  };

  return (
    <form className={styles.messageInputForm} onSubmit={handleSubmit}>
      <input
        type="text"
        className={styles.inputField}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message..."
      />
      <button type="submit" className={styles.sendButton}>Send</button>
    </form>
  );
};

export default MessageInput;
