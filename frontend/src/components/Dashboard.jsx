import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Database,
  FileText,
  Grid2X2,
  LogOut,
  MessageSquare,
  Pencil,
  Plus,
  Save,
  Send,
  Settings,
  Sparkles,
  X,
  Trash2,
  Upload,
  User,
} from 'lucide-react';
import { config } from '../config';

const passwordRule = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

export default function Dashboard() {
  const [selectedApp, setSelectedApp] = useState(() => localStorage.getItem('selected_app'));
  const [user, setUser] = useState(null);
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(() => localStorage.getItem('active_rag_session_id'));
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState({ state: 'idle', msg: '' });
  const [queryMode, setQueryMode] = useState('hybrid');
  const [previewChunks, setPreviewChunks] = useState([]);
  const [previewTitle, setPreviewTitle] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);
  const [profileForm, setProfileForm] = useState({ username: '', full_name: '', email: '', password: '' });
  const [profileStatus, setProfileStatus] = useState({ state: 'idle', msg: '' });
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const authHeaders = { Authorization: `Bearer ${token}` };

  const loadMessages = async (sessionId) => {
    const res = await axios.get(`${config.API_URL}/chats/${sessionId}/messages`, {
      headers: authHeaders,
    });
    setChatHistory(
      res.data.map((message) => ({
        q: message.question,
        a: message.answer,
        sources: message.sources || [],
      }))
    );
  };

  const loadDocuments = useCallback(async (sessionId = activeSessionId) => {
    if (!sessionId) {
      setDocuments([]);
      return;
    }
    const res = await axios.get(`${config.API_URL}/upload/documents`, {
      headers: authHeaders,
      params: { session_id: sessionId },
    });
    setDocuments(res.data);
  }, [token, activeSessionId]);

  const loadSessions = useCallback(async () => {
    const res = await axios.get(`${config.API_URL}/chats`, { headers: authHeaders });
    setSessions(res.data);
    return res.data;
  }, [token]);

  useEffect(() => {
    const initialize = async () => {
      try {
        const res = await axios.get(`${config.API_URL}/auth/me`, {
          headers: authHeaders,
        });
        setUser(res.data);
        setProfileForm({
          username: res.data.username || '',
          full_name: res.data.full_name || '',
          email: res.data.email || '',
          password: '',
        });
        const loadedSessions = await loadSessions();
        if (localStorage.getItem('selected_app') === 'rag' && loadedSessions.length > 0) {
          const savedSessionId = localStorage.getItem('active_rag_session_id');
          const sessionToOpen = loadedSessions.find((session) => session.id === savedSessionId) || loadedSessions[0];
          setActiveSessionId(sessionToOpen.id);
          localStorage.setItem('active_rag_session_id', sessionToOpen.id);
          await loadMessages(sessionToOpen.id);
          await loadDocuments(sessionToOpen.id);
        }
      } catch (err) {
        localStorage.removeItem('token');
        navigate('/login');
      }
    };
    initialize();
  }, [navigate, token, loadSessions]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isLoading]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const openApp = async (appName) => {
    setSelectedApp(appName);
    localStorage.setItem('selected_app', appName);

    if (appName === 'rag') {
      const loadedSessions = sessions.length > 0 ? sessions : await loadSessions();
      if (loadedSessions.length > 0 && !activeSessionId) {
        setActiveSessionId(loadedSessions[0].id);
        localStorage.setItem('active_rag_session_id', loadedSessions[0].id);
        await loadMessages(loadedSessions[0].id);
        await loadDocuments(loadedSessions[0].id);
      }
    }
  };

  const closeApp = () => {
    setSelectedApp(null);
    localStorage.removeItem('selected_app');
  };

  const createSession = async (title = 'New chat') => {
    const res = await axios.post(`${config.API_URL}/chats`, { title }, { headers: authHeaders });
    setSessions((prev) => [res.data, ...prev.filter((item) => item.id !== res.data.id)]);
    setActiveSessionId(res.data.id);
    localStorage.setItem('active_rag_session_id', res.data.id);
    setChatHistory([]);
    setDocuments([]);
    return res.data;
  };

  const handleNewChat = async () => {
    await createSession();
    setQuestion('');
    setUploadStatus({ state: 'idle', msg: '' });
  };

  const handleSelectChat = async (sessionId) => {
    if (editingSessionId) return;
    setActiveSessionId(sessionId);
    localStorage.setItem('active_rag_session_id', sessionId);
    await loadMessages(sessionId);
    await loadDocuments(sessionId);
  };

  const startRenameChat = (session, event) => {
    event.stopPropagation();
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const cancelRenameChat = (event) => {
    event?.stopPropagation();
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const saveRenameChat = async (sessionId, event) => {
    event?.stopPropagation();
    const title = editingTitle.trim();
    if (!title) return;

    const res = await axios.patch(
      `${config.API_URL}/chats/${sessionId}`,
      { title },
      { headers: authHeaders }
    );

    setSessions((prev) => prev.map((session) => (
      session.id === sessionId ? res.data : session
    )));
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const ensureActiveSession = async () => {
    if (activeSessionId) return activeSessionId;
    const session = await createSession();
    return session.id;
  };

  const refreshSessionsAfterQuery = (session) => {
    if (!session) return;
    setSessions((prev) => [session, ...prev.filter((item) => item.id !== session.id)]);
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const currentQ = question;
    const sessionId = await ensureActiveSession();
    setQuestion('');
    setIsLoading(true);

    try {
      const res = await axios.post(
        `${config.API_URL}/query`,
        { question: currentQ, session_id: sessionId, query_mode: queryMode },
        { headers: authHeaders },
      );

      setActiveSessionId(res.data.session.id);
      localStorage.setItem('active_rag_session_id', res.data.session.id);
      refreshSessionsAfterQuery(res.data.session);
      setChatHistory((prev) => [
        ...prev,
        { q: currentQ, a: res.data.answer, sources: res.data.sources },
      ]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        { q: currentQ, a: err.response?.data?.detail || 'Error connecting to the AI service.', sources: [] },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    const sessionId = await ensureActiveSession();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    setUploadStatus({ state: 'uploading', msg: 'Processing document...' });

    try {
      const res = await axios.post(`${config.API_URL}/upload/`, formData, {
        headers: {
          ...authHeaders,
          'Content-Type': 'multipart/form-data',
        },
      });
      setUploadStatus({ state: 'success', msg: res.data.message || 'Knowledge base updated!' });
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await loadDocuments(sessionId);
      setTimeout(() => setUploadStatus({ state: 'idle', msg: '' }), 4000);
    } catch (err) {
      setUploadStatus({ state: 'error', msg: err.response?.data?.detail || 'Upload failed' });
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!activeSessionId) return;
    try {
      await axios.delete(`${config.API_URL}/upload/documents/${documentId}`, {
        headers: authHeaders,
        params: { session_id: activeSessionId },
      });
      await loadDocuments(activeSessionId);
      setUploadStatus({ state: 'success', msg: 'File removed from this chat.' });
      setTimeout(() => setUploadStatus({ state: 'idle', msg: '' }), 3000);
    } catch (err) {
      setUploadStatus({ state: 'error', msg: err.response?.data?.detail || 'Failed to remove file' });
    }
  };

  const handleDeleteChat = async (sessionId, event) => {
    event.stopPropagation();
    await axios.delete(`${config.API_URL}/chats/${sessionId}`, { headers: authHeaders });
    const nextSessions = sessions.filter((session) => session.id !== sessionId);
    setSessions(nextSessions);
    if (activeSessionId === sessionId) {
      const next = nextSessions[0];
      if (next) {
        await handleSelectChat(next.id);
      } else {
        setActiveSessionId(null);
        localStorage.removeItem('active_rag_session_id');
        setChatHistory([]);
        setDocuments([]);
      }
    }
  };

  const handlePreviewDocument = async (document) => {
    const res = await axios.get(`${config.API_URL}/upload/documents/${document.id}/chunks`, {
      headers: authHeaders,
      params: { session_id: activeSessionId },
    });
    setPreviewTitle(document.filename);
    setPreviewChunks(res.data);
  };

  const handleReindexDocument = async (documentId) => {
    const res = await axios.post(`${config.API_URL}/upload/documents/${documentId}/reindex`, null, {
      headers: authHeaders,
      params: { session_id: activeSessionId },
    });
    setUploadStatus({ state: 'success', msg: res.data.message });
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    if (profileForm.password && !passwordRule.test(profileForm.password)) {
      setProfileStatus({ state: 'error', msg: 'Password needs uppercase, lowercase, number, and special character.' });
      return;
    }

    const payload = {
      username: profileForm.username,
      full_name: profileForm.full_name,
      email: profileForm.email,
    };
    if (profileForm.password) payload.password = profileForm.password;

    try {
      const res = await axios.put(`${config.API_URL}/auth/me`, payload, { headers: authHeaders });
      setUser(res.data);
      setProfileForm((prev) => ({ ...prev, password: '' }));
      setProfileStatus({ state: 'success', msg: 'Profile updated.' });
    } catch (err) {
      setProfileStatus({ state: 'error', msg: err.response?.data?.detail || 'Profile update failed' });
    }
  };

  const activeSession = sessions.find((session) => session.id === activeSessionId);

  if (!selectedApp) {
    return (
      <Shell user={user} onLogout={handleLogout} onProfile={() => setProfileOpen(true)}>
        <div className="max-w-6xl mx-auto w-full px-6 py-10">
          <div className="mb-8">
            <p className="text-sm font-bold uppercase tracking-widest text-cyan-300">Workspace</p>
            <h1 className="text-4xl font-bold text-white mt-2">Choose an app</h1>
            <p className="text-gray-400 mt-3 max-w-2xl">
              Start with the RAG Knowledge Base now. More apps can be added here later without changing the login flow.
            </p>
          </div>
          <button
            onClick={() => openApp('rag')}
            className="group text-left w-full max-w-md bg-surface/80 border border-cyan-500/30 hover:border-cyan-300 rounded-2xl p-6 shadow-2xl shadow-cyan-950/30 transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="p-4 rounded-2xl bg-cyan-400/15 text-cyan-300">
                <Database className="w-8 h-8" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">RAG Knowledge Base</h2>
                <p className="text-gray-400 text-sm mt-1">Chat with documents in session-specific workspaces.</p>
              </div>
            </div>
          </button>
        </div>
        {profileOpen && renderProfileModal()}
      </Shell>
    );
  }

  return (
    <Shell user={user} onLogout={handleLogout} onProfile={() => setProfileOpen(true)}>
      <main className="flex-1 w-full flex relative z-10 h-[calc(100vh-72px)]">
        <aside className="w-72 border-r border-gray-800 bg-[#10151f]/90 p-4 flex flex-col gap-4">
          <button
            onClick={closeApp}
            className="text-gray-400 hover:text-white flex items-center gap-2 text-sm mb-1"
          >
            <ArrowLeft className="w-4 h-4" /> Apps
          </button>
          <button
            onClick={handleNewChat}
            className="w-full bg-cyan-400 hover:bg-cyan-300 text-gray-950 px-4 py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all"
          >
            <Plus className="w-4 h-4" /> New chat
          </button>
          <div className="flex-1 overflow-y-auto space-y-2">
            {sessions.length === 0 ? (
              <p className="text-sm text-gray-500 px-2">No chats yet.</p>
            ) : (
              sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => handleSelectChat(session.id)}
                  className={`w-full text-left px-3 py-3 rounded-xl border transition-all ${
                    activeSessionId === session.id
                      ? 'bg-cyan-400/15 border-cyan-400/40 text-white'
                      : 'bg-gray-900/40 border-gray-800 text-gray-300 hover:text-white'
                  }`}
                >
                  {editingSessionId === session.id ? (
                    <div className="flex items-center gap-2" onClick={(event) => event.stopPropagation()}>
                      <input
                        autoFocus
                        value={editingTitle}
                        onChange={(event) => setEditingTitle(event.target.value)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') saveRenameChat(session.id, event);
                          if (event.key === 'Escape') cancelRenameChat(event);
                        }}
                        className="min-w-0 flex-1 bg-gray-950 border border-cyan-400/50 text-white rounded-lg px-2 py-1 text-sm focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={(event) => saveRenameChat(session.id, event)}
                        className="p-1.5 text-cyan-300 hover:text-white"
                        title="Save name"
                      >
                        <Save className="w-4 h-4" />
                      </button>
                      <button
                        type="button"
                        onClick={cancelRenameChat}
                        className="p-1.5 text-gray-500 hover:text-white"
                        title="Cancel"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 min-w-0 group">
                      <MessageSquare className="w-4 h-4 shrink-0" />
                      <span className="truncate text-sm flex-1">{session.title}</span>
                      <button
                        type="button"
                        onClick={(event) => startRenameChat(session, event)}
                        className="p-1 text-gray-500 hover:text-cyan-300 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-all"
                        title="Rename chat"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={(event) => handleDeleteChat(session.id, event)}
                        className="p-1 text-gray-500 hover:text-red-300 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-all"
                        title="Delete chat"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </button>
              ))
            )}
          </div>
        </aside>

        <section className="flex-1 flex flex-col bg-[#0b0f17]">
          <div className="px-6 py-4 border-b border-gray-800 bg-[#111827]/90 flex items-center justify-between">
            <div className="min-w-0">
              <p className="text-xs text-cyan-300 font-bold uppercase tracking-widest">RAG Knowledge Base</p>
              <h2 className="text-white font-semibold truncate">{activeSession?.title || 'New chat'}</h2>
            </div>
            <div className="text-sm text-gray-400 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-cyan-300" /> {documents.length} files
            </div>
          </div>

          <div className="flex-1 flex overflow-hidden">
            <div className="flex-1 flex flex-col">
              <div className="flex-1 overflow-y-auto p-6 space-y-8 scroll-smooth">
                {chatHistory.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-gray-500">
                    <div className="bg-cyan-400/10 p-6 rounded-3xl border border-cyan-400/20 shadow-2xl mb-6">
                      <Sparkles className="w-12 h-12 text-cyan-300" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Start a focused chat</h2>
                    <p className="text-gray-400 text-center max-w-md">
                      Upload files for this chat, then ask questions. A new chat starts with a fresh knowledge base.
                    </p>
                  </div>
                ) : (
                  chatHistory.map((chat, idx) => (
                    <div key={idx} className="space-y-6">
                      <div className="flex justify-end items-end gap-2">
                        <div className="bg-gradient-to-br from-cyan-400 to-indigo-500 text-white px-5 py-3.5 rounded-2xl rounded-tr-sm max-w-[75%] shadow-lg font-medium">
                          {chat.q}
                        </div>
                        <div className="w-8 h-8 rounded-full bg-gray-900 border border-gray-700 flex items-center justify-center shrink-0">
                          <User className="w-4 h-4 text-gray-400" />
                        </div>
                      </div>
                      <div className="flex justify-start items-end gap-2">
                        <div className="w-8 h-8 rounded-full bg-fuchsia-400/15 border border-fuchsia-300/30 flex items-center justify-center shrink-0">
                          <Sparkles className="w-4 h-4 text-fuchsia-300" />
                        </div>
                        <div className="bg-[#151b28] border border-gray-800 text-gray-200 px-6 py-5 rounded-2xl rounded-tl-sm max-w-[80%] shadow-lg">
                          <div className="text-sm leading-relaxed whitespace-pre-wrap">{chat.a}</div>
                          {chat.sources && chat.sources.length > 0 && (
                            <div className="mt-5 pt-4 border-t border-gray-800">
                              <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mb-3 flex items-center gap-1">
                                <BookOpen className="w-3 h-3" /> References
                              </p>
                              <div className="flex flex-col gap-2">
                                {chat.sources.map((src, i) => (
                                  <div key={i} className="text-xs bg-gray-950/50 p-3 rounded-lg border border-gray-800/50 text-gray-400 line-clamp-2">
                                    {typeof src === 'string'
                                      ? src
                                      : `${src.filename || 'Document'}${src.page_number ? `, page ${src.page_number}` : ''}, chunk ${src.chunk_index ?? i}: ${src.content || ''}`}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                {isLoading && (
                  <div className="flex justify-start items-end gap-2">
                    <div className="w-8 h-8 rounded-full bg-fuchsia-400/15 border border-fuchsia-300/30 flex items-center justify-center shrink-0">
                      <Sparkles className="w-4 h-4 text-fuchsia-300 animate-pulse" />
                    </div>
                    <div className="bg-[#151b28] border border-gray-800 px-6 py-4 rounded-2xl rounded-tl-sm shadow-lg flex gap-1.5 items-center">
                      <div className="w-2 h-2 bg-cyan-300 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-cyan-300 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-cyan-300 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="p-4 bg-[#111827] border-t border-gray-800">
                <div className="flex justify-end mb-3">
                  <div className="bg-gray-950/70 border border-gray-800 rounded-xl p-1 flex text-xs">
                    <button
                      type="button"
                      onClick={() => setQueryMode('hybrid')}
                      className={`px-3 py-1.5 rounded-lg ${queryMode === 'hybrid' ? 'bg-cyan-400 text-gray-950' : 'text-gray-400'}`}
                    >
                      Hybrid
                    </button>
                    <button
                      type="button"
                      onClick={() => setQueryMode('document_only')}
                      className={`px-3 py-1.5 rounded-lg ${queryMode === 'document_only' ? 'bg-cyan-400 text-gray-950' : 'text-gray-400'}`}
                    >
                      Documents only
                    </button>
                  </div>
                </div>
                <form onSubmit={handleQuery} className="flex gap-3">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask a question..."
                    className="flex-1 bg-gray-950/70 border border-gray-700 text-white px-5 py-4 rounded-xl focus:outline-none focus:border-cyan-300 focus:ring-1 focus:ring-cyan-300 transition-all placeholder-gray-500"
                    disabled={isLoading}
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !question.trim()}
                    className="bg-cyan-400 hover:bg-cyan-300 disabled:bg-gray-800 disabled:text-gray-500 text-gray-950 px-6 rounded-xl transition-all flex items-center justify-center shadow-lg shadow-cyan-950/40"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </form>
              </div>
            </div>

            <aside className="w-80 border-l border-gray-800 bg-[#10151f] p-5 overflow-y-auto">
              <h3 className="text-white font-semibold flex items-center gap-2 mb-5">
                <Upload className="w-5 h-5 text-cyan-300" />
                Chat knowledge base
              </h3>
              <form onSubmit={handleFileUpload} className="space-y-4">
                <div className="border-2 border-dashed border-gray-700 hover:border-cyan-300/70 bg-gray-950/30 transition-colors rounded-xl p-6 text-center cursor-pointer relative">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={config.SUPPORTED_FILES}
                    onChange={(e) => setFile(e.target.files[0])}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                  />
                  <Upload className="w-8 h-8 text-gray-500 mx-auto mb-3" />
                  <div className="text-sm font-medium text-gray-300">{file ? file.name : 'Drop file here'}</div>
                  <div className="text-xs text-gray-500 mt-1">This file belongs to the current chat.</div>
                </div>
                <button
                  type="submit"
                  disabled={!file || uploadStatus.state === 'uploading'}
                  className="w-full bg-cyan-400 hover:bg-cyan-300 disabled:bg-gray-800 disabled:text-gray-500 text-gray-950 font-semibold py-3 px-4 rounded-xl transition-all flex items-center justify-center gap-2"
                >
                  {uploadStatus.state === 'uploading' ? (
                    <div className="w-4 h-4 border-2 border-gray-600 border-t-gray-950 rounded-full animate-spin"></div>
                  ) : 'Process file'}
                </button>
              </form>

              {uploadStatus.state !== 'idle' && (
                <div className={`mt-4 text-sm flex items-center gap-2 p-3 rounded-xl border ${
                  uploadStatus.state === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-400' :
                  uploadStatus.state === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                  'bg-cyan-500/10 border-cyan-500/20 text-cyan-300'
                }`}>
                  {uploadStatus.state === 'success' && <CheckCircle2 className="w-4 h-4" />}
                  {uploadStatus.state === 'error' && <AlertCircle className="w-4 h-4" />}
                  {uploadStatus.msg}
                </div>
              )}

              <div className="mt-6 space-y-3">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">Files in this chat</p>
                {documents.length === 0 ? (
                  <p className="text-sm text-gray-500">No files uploaded for this chat.</p>
                ) : (
                  documents.map((document) => (
                    <div key={document.id} className="bg-gray-950/40 border border-gray-800 rounded-xl p-3 text-gray-300 flex gap-3">
                      <FileText className="w-4 h-4 text-cyan-300 shrink-0 mt-0.5" />
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm">{document.filename}</div>
                        <div className="text-xs text-gray-500">{document.chunk_count} chunks</div>
                      </div>
                      <button
                        onClick={() => handlePreviewDocument(document)}
                        className="p-1.5 text-gray-500 hover:text-cyan-300 transition-colors"
                        title="Preview chunks"
                      >
                        <BookOpen className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleReindexDocument(document.id)}
                        className="p-1.5 text-gray-500 hover:text-green-300 transition-colors"
                        title="Re-index"
                      >
                        <Sparkles className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteDocument(document.id)}
                        className="p-1.5 text-gray-500 hover:text-red-300 transition-colors"
                        title="Remove file"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </aside>
          </div>
        </section>
      </main>
      {previewChunks.length > 0 && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 w-full max-w-3xl max-h-[80vh] overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white truncate">{previewTitle}</h2>
              <button onClick={() => setPreviewChunks([])} className="text-gray-400 hover:text-white">Close</button>
            </div>
            <div className="overflow-y-auto max-h-[62vh] space-y-3 pr-2">
              {previewChunks.map((chunk, index) => (
                <div key={index} className="bg-gray-950/60 border border-gray-800 rounded-xl p-4">
                  <div className="text-xs text-cyan-300 mb-2">Chunk {chunk.chunk_index ?? index}</div>
                  <div className="text-sm text-gray-300 whitespace-pre-wrap">{chunk.content}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      {profileOpen && renderProfileModal()}
    </Shell>
  );

  function renderProfileModal() {
    return (
      <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
        <div className="bg-[#111827] border border-gray-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-bold text-white">Profile</h2>
            <button onClick={() => setProfileOpen(false)} className="text-gray-400 hover:text-white">Close</button>
          </div>
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <input className="w-full bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 text-white" placeholder="Username" value={profileForm.username} onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })} />
            <input className="w-full bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 text-white" placeholder="Full name" value={profileForm.full_name} onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })} />
            <input className="w-full bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 text-white" placeholder="Email" value={profileForm.email} onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })} />
            <input className="w-full bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 text-white" type="password" placeholder="New password" value={profileForm.password} onChange={(e) => setProfileForm({ ...profileForm, password: e.target.value })} />
            <p className="text-xs text-gray-500">Leave password empty to keep the current one.</p>
            {profileStatus.state !== 'idle' && (
              <div className={`text-sm ${profileStatus.state === 'success' ? 'text-green-400' : 'text-red-400'}`}>{profileStatus.msg}</div>
            )}
            <button className="w-full bg-cyan-400 hover:bg-cyan-300 text-gray-950 font-semibold py-3 rounded-xl">Save profile</button>
          </form>
        </div>
      </div>
    );
  }
}

function Shell({ children, user, onLogout, onProfile }) {
  return (
    <div className="min-h-screen bg-[#090d14] text-gray-100 flex flex-col font-sans">
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.14),transparent_32%),radial-gradient(circle_at_bottom_right,rgba(217,70,239,0.12),transparent_35%)]"></div>
      <header className="relative z-10 h-[72px] border-b border-gray-800 bg-[#0f1623]/90 backdrop-blur-xl px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-400/15 text-cyan-300">
            <Grid2X2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-white font-bold">{config.APP_NAME}</div>
            <div className="text-xs text-gray-500">Application workspace</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={onProfile} className="flex items-center gap-2 bg-gray-900/80 border border-gray-800 hover:border-cyan-400/50 rounded-xl px-3 py-2 transition-all">
            <User className="w-4 h-4 text-cyan-300" />
            <span className="text-sm text-gray-200">{user?.username || 'Profile'}</span>
            <Settings className="w-4 h-4 text-gray-500" />
          </button>
          <button onClick={onLogout} className="p-2.5 text-gray-400 hover:text-white hover:bg-red-500/15 rounded-xl transition-all" title="Logout">
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </header>
      <div className="relative z-10 flex-1 flex">{children}</div>
    </div>
  );
}
