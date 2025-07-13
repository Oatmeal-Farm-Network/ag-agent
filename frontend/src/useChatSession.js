import { useState, useEffect, useRef, useCallback } from 'react';

// This custom hook encapsulates all chat logic
export const useChatSession = (userId) => {
    // State for the hook
    const [sessions, setSessions] = useState([]); // List of all past chat sessions
    const [currentSessionId, setCurrentSessionId] = useState(null); // The active session ID
    const [messages, setMessages] = useState([]); // Messages for the active session
    const [thinkingSteps, setThinkingSteps] = useState([]);
    const [isThinking, setIsThinking] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const ws = useRef(null);

    const backendHost = process.env.REACT_APP_BACKEND_HOST || 'localhost:8000';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${backendHost}/ws/chat`;

    // Function to connect to WebSocket
    const connect = useCallback(() => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) return;

        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => setIsConnected(true);
        ws.current.onclose = () => setIsConnected(false);
        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.type) {
                case 'session_created':
                    setCurrentSessionId(data.session_id); // Backend provides the new session ID
                    // Here you would also fetch the updated list of all sessions
                    break;
                case 'agent_step':
                    setIsThinking(true);
                    setThinkingSteps(prev => [...prev, { agent_name: data.agent_name, id: Date.now() }]);
                    break;
                case 'final_answer':
                    setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
                    setIsThinking(false);
                    setThinkingSteps([]);
                    break;
                case 'error':
                    setMessages(prev => [...prev, { id: Date.now(), text: data.content, sender: 'ai' }]);
                    setIsThinking(false);
                    setThinkingSteps([]);
                    break;
                default:
                    break;
            }
        };
    }, [wsUrl]);

    // Initial connection
    useEffect(() => {
        if (userId) {
            connect();
            // In a real app, you would fetch the initial list of sessions here
            // fetchSessions(userId).then(setSessions);
        }
        return () => ws.current?.close();
    }, [userId, connect]);

    // Function to send a message
    const sendMessage = useCallback((payload) => {
        if (ws.current?.readyState !== WebSocket.OPEN) {
            console.error("WebSocket is not connected.");
            return;
        }
        const messageToSend = {
            ...payload,
            user_id: userId,
            session_id: currentSessionId, // Automatically sends the current session ID
        };
        ws.current.send(JSON.stringify(messageToSend));
        if (payload.text) {
            setMessages(prev => [...prev, { id: Date.now(), text: payload.text, sender: 'user', images: payload.images }]);
        }
    }, [userId, currentSessionId]);

    // Function to start a new chat
    const startNewChat = useCallback(() => {
        setCurrentSessionId(null); // This signals the backend to create a new session on the next message
        setMessages([{ id: 1, text: "Hello! How can I help you today?", sender: "ai" }]);
        setIsThinking(false);
        setThinkingSteps([]);
    }, []);

    // Function to select an existing chat (you would implement this with an API call)
    const selectSession = useCallback((sessionId) => {
        setCurrentSessionId(sessionId);
        // In a real app, you would fetch the message history for this session
        // fetchMessagesForSession(sessionId).then(setMessages);
    }, []);


    return { sessions, messages, sendMessage, startNewChat, selectSession, isThinking, thinkingSteps };
};