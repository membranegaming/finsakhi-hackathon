import { useState, useEffect, useRef } from 'react';
import { useApp } from '../contexts/AppContext';
import { useAuth } from '../store/authStore.jsx';
import { chatAPI } from '../services/api';
import './Mentor.css';

export default function Mentor({ userId: propUserId }) {
  const { language } = useApp();
  const auth = useAuth();
  const userId = propUserId || auth.userId;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (userId) loadConversations();
  }, [userId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversations = async () => {
    try {
      const res = await chatAPI.getConversations(userId);
      setConversations(res.conversations || []);
    } catch (e) { console.error(e); }
  };

  const loadConversation = async (convId) => {
    try {
      const res = await chatAPI.getConversationMessages(userId, convId);
      const msgs = (res.messages || []).map(m => ({
        role: m.role,
        content: m.content || m.message,
      }));
      setMessages(msgs);
      setConversationId(convId);
      setShowHistory(false);
    } catch (e) { console.error(e); }
  };

  const startNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setSuggestions([]);
    setShowHistory(false);
  };

  const sendMessage = async (text) => {
    const msg = text || input.trim();
    if (!msg || sending) return;

    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setInput('');
    setSending(true);

    try {
      const res = await chatAPI.sendMessage(userId, msg, conversationId, language);
      setConversationId(res.conversation_id);
      setMessages(prev => [...prev, { role: 'assistant', content: res.reply }]);
      setSuggestions(res.suggestions || []);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}` }]);
    }
    setSending(false);
  };

  const quickPrompts = language === 'hi'
    ? ['मुझे बचत के बारे में बताओ', 'म्यूचुअल फंड क्या है?', 'मेरे लिए कौन सी सरकारी योजना अच्छी है?', 'EMI कैसे कम करें?']
    : ['Tell me about saving money', 'What are mutual funds?', 'Which govt schemes am I eligible for?', 'How to reduce EMI burden?'];

  return (
    <div className="mentor-page" style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', flexShrink: 0 }}>
        <div>
          <h1 style={{ fontSize: '1.3rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            🤖 {language === 'hi' ? 'AI वित्तीय सलाहकार' : 'AI Financial Mentor'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.15rem' }}>
            {language === 'hi' ? 'आपकी वित्तीय प्रोफ़ाइल के आधार पर व्यक्तिगत सलाह' : 'Personalized advice based on your financial profile'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={() => setShowHistory(!showHistory)}
            style={{ padding: '0.4rem 0.8rem', borderRadius: '8px', border: '1px solid var(--border-subtle)', background: 'var(--card-bg)', cursor: 'pointer', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
            📜 {language === 'hi' ? 'इतिहास' : 'History'}
          </button>
          <button onClick={startNewChat}
            style={{ padding: '0.4rem 0.8rem', borderRadius: '8px', border: '1px solid var(--border-subtle)', background: 'var(--accent-primary)', color: '#fff', cursor: 'pointer', fontSize: '0.8rem' }}>
            + {language === 'hi' ? 'नई चैट' : 'New Chat'}
          </button>
        </div>
      </div>

      {/* Conversation history sidebar */}
      {showHistory && (
        <div style={{ background: 'var(--card-bg)', borderRadius: '12px', padding: '0.75rem', marginBottom: '0.75rem', border: '1px solid var(--border-subtle)', maxHeight: '200px', overflowY: 'auto', flexShrink: 0 }}>
          <h3 style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>{language === 'hi' ? 'पिछली बातचीत' : 'Past Conversations'}</h3>
          {conversations.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{language === 'hi' ? 'कोई पिछली बातचीत नहीं' : 'No past conversations'}</p>
          ) : conversations.map((c, i) => (
            <div key={i} onClick={() => loadConversation(c.conversation_id)}
              style={{ padding: '0.5rem 0.75rem', borderRadius: '8px', cursor: 'pointer', marginBottom: '0.25rem', background: conversationId === c.conversation_id ? 'var(--bg-secondary)' : 'transparent', fontSize: '0.8rem' }}>
              <div style={{ fontWeight: 500 }}>{c.preview || `Chat ${i + 1}`}</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem' }}>{c.message_count} messages</div>
            </div>
          ))}
        </div>
      )}

      {/* Messages area */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem', padding: '0.5rem 0', minHeight: 0 }}>
        {messages.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
            <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>💬</div>
            <p style={{ fontSize: '1rem', marginBottom: '1.25rem' }}>
              {language === 'hi' ? 'नमस्ते! मुझसे कुछ भी पूछें।' : 'Hi! Ask me anything about finance.'}
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center', maxWidth: '500px' }}>
              {quickPrompts.map((prompt, i) => (
                <button key={i} onClick={() => sendMessage(prompt)}
                  style={{ padding: '0.5rem 0.9rem', borderRadius: '20px', border: '1px solid var(--border-subtle)', background: 'var(--card-bg)', cursor: 'pointer', fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div style={{
                maxWidth: '80%', padding: '0.75rem 1rem', borderRadius: '16px',
                background: msg.role === 'user' ? 'var(--accent-primary)' : 'var(--card-bg)',
                color: msg.role === 'user' ? '#fff' : 'var(--text-primary)',
                border: msg.role === 'user' ? 'none' : '1px solid var(--border-subtle)',
                whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: 1.6
              }}>
                {msg.content}
              </div>
            </div>
          ))
        )}

        {sending && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ padding: '0.75rem 1rem', borderRadius: '16px', background: 'var(--card-bg)', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
              ⏳ {language === 'hi' ? 'सोच रहा हूँ...' : 'Thinking...'}
            </div>
          </div>
        )}

        {/* Suggestions */}
        {suggestions.length > 0 && !sending && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {suggestions.map((s, i) => (
              <button key={i} onClick={() => sendMessage(s)}
                style={{ padding: '0.35rem 0.75rem', borderRadius: '16px', border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', cursor: 'pointer', fontSize: '0.75rem', color: 'var(--text-primary)' }}>
                {s}
              </button>
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div style={{ display: 'flex', gap: '0.5rem', padding: '0.75rem 0', flexShrink: 0 }}>
        <input type="text"
          placeholder={language === 'hi' ? 'अपना सवाल लिखें...' : 'Type your question...'}
          value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          disabled={sending}
          style={{ flex: 1, padding: '0.75rem 1rem', borderRadius: '12px', border: '1px solid var(--border-subtle)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.9rem' }} />
        <button onClick={() => sendMessage()} disabled={sending || !input.trim()}
          style={{ padding: '0.75rem 1.25rem', borderRadius: '12px', background: 'var(--accent-primary)', color: '#fff', border: 'none', cursor: 'pointer', fontSize: '0.9rem' }}>
          ➤
        </button>
      </div>
    </div>
  );
}

