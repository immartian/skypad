import React, { useEffect, useRef } from 'react';
import styles from './MessageList.module.css';
import MessageItem from '../MessageItem/MessageItem';
import type { Message } from '../ChatPage/ChatPage';

interface MessageListProps {
  messages: Message[];
  isOldMessages?: boolean; // New prop to indicate if this list is for old messages
}

const MessageList: React.FC<MessageListProps> = ({ messages, isOldMessages }) => {
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const messageListRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (isOldMessages) {
      // For old messages (flex-direction: column-reverse), we want to keep scroll at bottom (which is visually the top)
      // or allow user to scroll freely. For now, no specific scroll-to-top logic on new old messages.
      // If new "old" messages are added, the container's column-reverse will place them appropriately.
    } else {
      // For recent messages, scroll to the newest message at the bottom.
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    // Scroll to bottom only for the recent messages list, or if old messages list is not reversed
    if (!isOldMessages) {
        scrollToBottom();
    }
    // If it's old messages and column-reverse, new messages appear at the "bottom" of the flex container,
    // which is visually the top. If we want to maintain scroll position when new old messages are added,
    // more complex logic would be needed, e.g., scroll to top if at top, or maintain current view.
    // For now, `column-reverse` handles the visual stacking.
  }, [messages, isOldMessages]);

  return (
    <div ref={messageListRef} className={`${styles.messageList} ${isOldMessages ? styles.oldMessageList : ''}`}>
      {messages.map((msg, index) => (
        <MessageItem
          key={msg.id}
          text={msg.text}
          sender={msg.sender}
          // Apply dimming for old messages: dim messages if their index is less than (length - 2).
          // This means the two "newest" messages in the oldMessages array (visually at the bottom of the old messages area)
          // will not be dimmed. Older messages (visually higher up) will be dimmed.
          isDimmed={isOldMessages && index < messages.length - 2}
        />
      ))}
      {!isOldMessages && <div ref={messagesEndRef} />}
    </div>
  );
};

export default MessageList;
