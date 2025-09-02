import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Label } from './components/ui/label';
import { Progress } from './components/ui/progress';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/sonner';
import { 
  MessageCircle, 
  FileText, 
  Ticket, 
  Upload, 
  Send, 
  Plus, 
  BarChart3, 
  Settings,
  Bot,
  Users,
  Calendar,
  CheckCircle,
  AlertCircle,
  Clock,
  FileUp,
  MessageSquare,
  TrendingUp,
  Filter,
  Search,
  User,
  Edit,
  Eye,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  PlayCircle,
  PauseCircle,
  MoreHorizontal
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Custom hook for API calls
const useAPI = () => {
  const { toast } = useToast();

  const apiCall = async (method, endpoint, data = null, isFormData = false) => {
    try {
      const config = {
        method,
        url: `${API}${endpoint}`,
        headers: isFormData ? {} : { 'Content-Type': 'application/json' },
      };
      
      if (data) config.data = data;
      
      const response = await axios(config);
      return response.data;
    } catch (error) {
      console.error(`API Error (${method} ${endpoint}):`, error);
      toast({
        title: "Error",
        description: error.response?.data?.detail || error.message,
        variant: "destructive"
      });
      throw error;
    }
  };

  return { apiCall };
};

// Main Dashboard Component
const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const { apiCall } = useAPI();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiCall('GET', '/dashboard/stats');
        setStats(data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };
    fetchStats();
  }, []);

  if (!stats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">ASI OS Dashboard</h1>
          <p className="text-gray-600 mt-2">AI-Powered Operations Platform</p>
        </div>
        <Badge variant="outline" className="text-emerald-600 border-emerald-200">
          <Bot className="w-4 h-4 mr-1" />
          AI Enhanced
        </Badge>
      </div>

      {/* Enhanced Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-emerald-700">Total Tickets</CardTitle>
            <Ticket className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-900">{stats.total_tickets}</div>
            <p className="text-xs text-emerald-600 mt-1">All support requests</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-700">Open Tickets</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-900">{stats.open_tickets}</div>
            <p className="text-xs text-orange-600 mt-1">Awaiting resolution</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">Documents</CardTitle>
            <FileText className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">{stats.total_documents}</div>
            <p className="text-xs text-blue-600 mt-1">Knowledge base files</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-700">Overdue</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-900">{stats.overdue_tickets}</div>
            <p className="text-xs text-red-600 mt-1">Past SLA deadline</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Tickets by Department</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.tickets_by_department?.map((dept) => (
                <div key={dept._id} className="flex items-center justify-between">
                  <span className="text-sm font-medium">{dept._id}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-emerald-600 h-2 rounded-full" 
                        style={{width: `${(dept.count / stats.total_tickets) * 100}%`}}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600">{dept.count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tickets by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.tickets_by_status?.map((status) => (
                <div key={status._id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {status._id === 'open' && <AlertCircle className="w-4 h-4 text-orange-500" />}
                    {status._id === 'in_progress' && <PlayCircle className="w-4 h-4 text-blue-500" />}
                    {status._id === 'resolved' && <CheckCircle2 className="w-4 h-4 text-green-500" />}
                    {status._id === 'closed' && <XCircle className="w-4 h-4 text-gray-500" />}
                    <span className="text-sm font-medium capitalize">{status._id.replace('_', ' ')}</span>
                  </div>
                  <Badge variant="outline">{status.count}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600" />
            Quick Actions
          </CardTitle>
          <CardDescription>Common operations and workflows</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link to="/chat">
              <Button className="w-full h-20 flex flex-col gap-2 bg-emerald-600 hover:bg-emerald-700">
                <MessageCircle className="w-6 h-6" />
                <span>Start AI Chat</span>
              </Button>
            </Link>
            <Link to="/tickets">
              <Button variant="outline" className="w-full h-20 flex flex-col gap-2 border-emerald-200 hover:bg-emerald-50">
                <Ticket className="w-6 h-6 text-emerald-600" />
                <span>View Tickets</span>
              </Button>
            </Link>
            <Link to="/documents">
              <Button variant="outline" className="w-full h-20 flex flex-col gap-2 border-emerald-200 hover:bg-emerald-50">
                <FileText className="w-6 h-6 text-emerald-600" />
                <span>Manage Documents</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// RAG Chat Component
const ChatInterface = () => {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [documentsCount, setDocumentsCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    fetchSessions();
    fetchDocumentsCount();
  }, []);

  const fetchSessions = async () => {
    try {
      const data = await apiCall('GET', '/chat/sessions');
      setSessions(data);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const fetchDocuments = async () => {
    try {
      const data = await apiCall('GET', '/documents');
      setDocuments(data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const fetchMessages = async (sessionId) => {
    try {
      const data = await apiCall('GET', `/chat/sessions/${sessionId}/messages`);
      setMessages(data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const startNewSession = () => {
    const newSessionId = `session-${Date.now()}`;
    setCurrentSession(newSessionId);
    setMessages([]);
  };

  const selectSession = (session) => {
    setCurrentSession(session.id);
    fetchMessages(session.id);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !currentSession) return;

    setLoading(true);
    try {
      const data = await apiCall('POST', '/chat/send', {
        session_id: currentSession,
        message: inputMessage,
        document_ids: selectedDocs
      });

      // Add messages to UI
      const userMsg = {
        role: 'user',
        content: inputMessage,
        timestamp: new Date().toISOString(),
        attachments: selectedDocs
      };
      const aiMsg = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, userMsg, aiMsg]);
      setInputMessage('');
      setSelectedDocs([]);

      // Show ticket suggestion if available
      if (data.suggested_ticket) {
        toast({
          title: "Ticket Creation Suggested",
          description: "This query might require a support ticket. Would you like to create one?",
        });
      }

      // Refresh sessions
      fetchSessions();
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">AI Assistant</h2>
            <Badge variant="outline" className="text-emerald-600 border-emerald-200">
              <Bot className="w-3 h-3 mr-1" />
              GPT-5
            </Badge>
          </div>
          <Button onClick={startNewSession} className="w-full bg-emerald-600 hover:bg-emerald-700">
            <Plus className="w-4 h-4 mr-2" />
            New Conversation
          </Button>
        </div>

        {/* Document Selection */}
        <div className="p-4 border-b border-gray-200">
          <Label className="text-sm font-medium text-gray-700 mb-2 block">Reference Documents</Label>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={doc.id}
                  checked={selectedDocs.includes(doc.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedDocs([...selectedDocs, doc.id]);
                    } else {
                      setSelectedDocs(selectedDocs.filter(id => id !== doc.id));
                    }
                  }}
                  className="rounded border-gray-300"
                />
                <Label htmlFor={doc.id} className="text-xs text-gray-600 truncate flex-1">
                  {doc.original_name}
                </Label>
              </div>
            ))}
          </div>
        </div>

        {/* Session History */}
        <div className="flex-1 overflow-y-auto p-4">
          <Label className="text-sm font-medium text-gray-700 mb-3 block">Recent Conversations</Label>
          <div className="space-y-2">
            {sessions.map((session) => (
              <Button
                key={session.id}
                variant={currentSession === session.id ? "default" : "ghost"}
                className="w-full justify-start text-left p-3 h-auto"
                onClick={() => selectSession(session)}
              >
                <div className="truncate">
                  <div className="font-medium text-sm truncate">{session.title}</div>
                  <div className="text-xs text-gray-500">
                    {session.messages_count} messages
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentSession ? (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-20">
                  <Bot className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
                  <p>Ask questions about your policies, create tickets, or get operational guidance.</p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-3xl rounded-lg p-4 ${
                      message.role === 'user' 
                        ? 'bg-emerald-600 text-white' 
                        : 'bg-white border border-gray-200'
                    }`}>
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                      {message.attachments && message.attachments.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-emerald-500 border-opacity-30">
                          <div className="text-xs opacity-75">
                            Referenced {message.attachments.length} document(s)
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-200 p-6">
              {selectedDocs.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {selectedDocs.map((docId) => {
                    const doc = documents.find(d => d.id === docId);
                    return doc ? (
                      <Badge key={docId} variant="secondary" className="text-xs">
                        <FileText className="w-3 h-3 mr-1" />
                        {doc.original_name}
                      </Badge>
                    ) : null;
                  })}
                </div>
              )}
              <div className="flex space-x-3">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask about policies, create tickets, or get guidance..."
                  className="flex-1"
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                />
                <Button 
                  onClick={sendMessage} 
                  disabled={loading || !inputMessage.trim()}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <MessageCircle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-xl font-medium mb-2">Welcome to AI Assistant</h3>
              <p className="text-gray-600 mb-6">Start a new conversation to get help with operations, policies, and support.</p>
              <Button onClick={startNewSession} className="bg-emerald-600 hover:bg-emerald-700">
                <Plus className="w-4 h-4 mr-2" />
                Start New Conversation
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Document Management Component
const DocumentManagement = () => {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const data = await apiCall('GET', '/documents');
      setDocuments(data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const data = await apiCall('POST', '/documents/upload', formData, true);
      
      toast({
        title: "Success",
        description: `${data.filename} uploaded successfully`,
      });
      
      fetchDocuments();
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Document Management</h1>
          <p className="text-gray-600 mt-2">Upload and manage policy documents for AI assistance</p>
        </div>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-emerald-600" />
            Upload Documents
          </CardTitle>
          <CardDescription>
            Upload PDF, DOCX, or TXT files to enhance the AI knowledge base
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-emerald-400 transition-colors">
            <FileUp className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              {uploading ? 'Uploading...' : 'Choose files to upload'}
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Supports PDF, DOCX, and TXT files
            </p>
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
              id="file-upload"
            />
            <Label htmlFor="file-upload">
              <Button asChild className="bg-emerald-600 hover:bg-emerald-700" disabled={uploading}>
                <span>
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Select Files
                    </>
                  )}
                </span>
              </Button>
            </Label>
          </div>
        </CardContent>
      </Card>

      {/* Documents List */}
      <Card>
        <CardHeader>
          <CardTitle>Uploaded Documents</CardTitle>
          <CardDescription>
            {documents.length} document(s) available for AI assistance
          </CardDescription>
        </CardHeader>
        <CardContent>
          {documents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No documents uploaded yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div className="flex items-center space-x-3">
                    <FileText className="w-8 h-8 text-emerald-600" />
                    <div>
                      <h3 className="font-medium text-gray-900">{doc.original_name}</h3>
                      <p className="text-sm text-gray-500">
                        Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </Badge>
                    {doc.department && (
                      <Badge variant="secondary">{doc.department}</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Enhanced Ticket Management Component  
const TicketManagement = () => {
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [ticketComments, setTicketComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    department: ''
  });
  const [newTicket, setNewTicket] = useState({
    subject: '',
    description: '',
    department: '',
    priority: 'medium',
    requester_name: 'System User'
  });
  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    fetchTickets();
  }, [filters]);

  const fetchTickets = async () => {
    try {
      const queryParams = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) queryParams.append(key, value);
      });
      
      const endpoint = queryParams.toString() ? `/tickets?${queryParams}` : '/tickets';
      const data = await apiCall('GET', endpoint);
      setTickets(data);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    }
  };

  const fetchTicketComments = async (ticketId) => {
    try {
      const data = await apiCall('GET', `/tickets/${ticketId}/comments`);
      setTicketComments(data);
    } catch (error) {
      console.error('Error fetching comments:', error);
    }
  };

  const createTicket = async () => {
    try {
      await apiCall('POST', '/tickets', newTicket);
      toast({
        title: "Success",
        description: "Ticket created successfully",
      });
      setShowCreateModal(false);
      setNewTicket({ 
        subject: '', 
        description: '', 
        department: '', 
        priority: 'medium',
        requester_name: 'System User'
      });
      fetchTickets();
    } catch (error) {
      console.error('Error creating ticket:', error);
    }
  };

  const updateTicketStatus = async (ticketId, status) => {
    try {
      await apiCall('PUT', `/tickets/${ticketId}`, { status });
      toast({
        title: "Success",
        description: `Ticket status updated to ${status}`,
      });
      fetchTickets();
      if (selectedTicket && selectedTicket.id === ticketId) {
        const updatedTicket = await apiCall('GET', `/tickets/${ticketId}`);
        setSelectedTicket(updatedTicket);
      }
    } catch (error) {
      console.error('Error updating ticket:', error);
    }
  };

  const addComment = async () => {
    if (!newComment.trim() || !selectedTicket) return;

    try {
      await apiCall('POST', `/tickets/${selectedTicket.id}/comments`, {
        content: newComment,
        comment_type: 'public',
        author_name: 'Support Agent'
      });
      
      setNewComment('');
      fetchTicketComments(selectedTicket.id);
      toast({
        title: "Success",
        description: "Comment added successfully",
      });
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  };

  const openTicketDetail = (ticket) => {
    setSelectedTicket(ticket);
    fetchTicketComments(ticket.id);
    setShowDetailModal(true);
  };

  const getStatusColor = (status) => {
    const colors = {
      open: 'bg-orange-100 text-orange-700 border-orange-200',
      in_progress: 'bg-blue-100 text-blue-700 border-blue-200',
      waiting_customer: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      resolved: 'bg-green-100 text-green-700 border-green-200',
      closed: 'bg-gray-100 text-gray-700 border-gray-200'
    };
    return colors[status] || colors.open;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'bg-gray-100 text-gray-700 border-gray-200',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      high: 'bg-orange-100 text-orange-700 border-orange-200',
      urgent: 'bg-red-100 text-red-700 border-red-200'
    };
    return colors[priority] || colors.medium;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'open': return <AlertCircle className="w-4 h-4" />;
      case 'in_progress': return <PlayCircle className="w-4 h-4" />;
      case 'waiting_customer': return <PauseCircle className="w-4 h-4" />;
      case 'resolved': return <CheckCircle2 className="w-4 h-4" />;
      case 'closed': return <XCircle className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Support Tickets</h1>
          <p className="text-gray-600 mt-2">Manage and track support requests</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="bg-emerald-600 hover:bg-emerald-700">
          <Plus className="w-4 h-4 mr-2" />
          Create Ticket
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Status</Label>
              <Select value={filters.status} onValueChange={(value) => setFilters({...filters, status: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All statuses</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="waiting_customer">Waiting Customer</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Priority</Label>
              <Select value={filters.priority} onValueChange={(value) => setFilters({...filters, priority: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="All priorities" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All priorities</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Department</Label>
              <Select value={filters.department} onValueChange={(value) => setFilters({...filters, department: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="All departments" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All departments</SelectItem>
                  <SelectItem value="User & Access Management">User & Access Management</SelectItem>
                  <SelectItem value="System & IT Support">System & IT Support</SelectItem>
                  <SelectItem value="Finance & Purchasing">Finance & Purchasing</SelectItem>
                  <SelectItem value="Leave & People Management">Leave & People Management</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tickets List */}
      <Card>
        <CardHeader>
          <CardTitle>All Tickets</CardTitle>
          <CardDescription>
            {tickets.length} ticket(s) found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {tickets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Ticket className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No tickets found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {tickets.map((ticket) => (
                <div key={ticket.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-medium text-gray-900">{ticket.subject}</h3>
                        <Badge variant="outline" className="text-xs">
                          {ticket.ticket_number}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{ticket.description}</p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span className="flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {new Date(ticket.created_at).toLocaleDateString()}
                        </span>
                        <span className="flex items-center">
                          <User className="w-3 h-3 mr-1" />
                          {ticket.requester_name}
                        </span>
                        <span>{ticket.department}</span>
                        {ticket.category && <span>• {ticket.category}</span>}
                      </div>
                    </div>
                    <div className="flex flex-col items-end space-y-2">
                      <div className="flex items-center space-x-2">
                        <Badge className={getStatusColor(ticket.status)}>
                          {getStatusIcon(ticket.status)}
                          <span className="ml-1 capitalize">{ticket.status.replace('_', ' ')}</span>
                        </Badge>
                        <Badge className={getPriorityColor(ticket.priority)}>
                          {ticket.priority}
                        </Badge>
                      </div>
                      <div className="flex space-x-1">
                        <Button size="sm" variant="outline" onClick={() => openTicketDetail(ticket)}>
                          <Eye className="w-3 h-3" />
                        </Button>
                        <Select onValueChange={(value) => updateTicketStatus(ticket.id, value)}>
                          <SelectTrigger className="w-8 h-8 p-0">
                            <MoreHorizontal className="w-3 h-3" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="open">Set Open</SelectItem>
                            <SelectItem value="in_progress">Set In Progress</SelectItem>
                            <SelectItem value="waiting_customer">Set Waiting Customer</SelectItem>
                            <SelectItem value="resolved">Set Resolved</SelectItem>
                            <SelectItem value="closed">Set Closed</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Ticket Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Create New Ticket</DialogTitle>
            <DialogDescription>
              Create a new support request with automatic AI categorization
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                value={newTicket.subject}
                onChange={(e) => setNewTicket({...newTicket, subject: e.target.value})}
                placeholder="Brief description of the issue"
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={newTicket.description}
                onChange={(e) => setNewTicket({...newTicket, description: e.target.value})}
                placeholder="Detailed description of the issue"
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="department">Department</Label>
                <Select value={newTicket.department} onValueChange={(value) => setNewTicket({...newTicket, department: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="User & Access Management">User & Access Management</SelectItem>
                    <SelectItem value="Contracts & Change Log">Contracts & Change Log</SelectItem>
                    <SelectItem value="Finance & Purchasing">Finance & Purchasing</SelectItem>
                    <SelectItem value="Project & Performance">Project & Performance</SelectItem>
                    <SelectItem value="Leave & People Management">Leave & People Management</SelectItem>
                    <SelectItem value="System & IT Support">System & IT Support</SelectItem>
                    <SelectItem value="Knowledge Base Requests">Knowledge Base Requests</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="priority">Priority</Label>
                <Select value={newTicket.priority} onValueChange={(value) => setNewTicket({...newTicket, priority: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label htmlFor="requester">Requester Name</Label>
              <Input
                id="requester"
                value={newTicket.requester_name}
                onChange={(e) => setNewTicket({...newTicket, requester_name: e.target.value})}
                placeholder="Name of person requesting support"
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button onClick={createTicket} className="bg-emerald-600 hover:bg-emerald-700">
                Create Ticket
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Ticket Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
          {selectedTicket && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center justify-between">
                  <span>{selectedTicket.subject}</span>
                  <Badge variant="outline">{selectedTicket.ticket_number}</Badge>
                </DialogTitle>
                <DialogDescription>
                  Created {new Date(selectedTicket.created_at).toLocaleDateString()} by {selectedTicket.requester_name}
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-6">
                {/* Ticket Details */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium">Status</Label>
                    <Badge className={`${getStatusColor(selectedTicket.status)} mt-1`}>
                      {getStatusIcon(selectedTicket.status)}
                      <span className="ml-1 capitalize">{selectedTicket.status.replace('_', ' ')}</span>
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Priority</Label>
                    <Badge className={`${getPriorityColor(selectedTicket.priority)} mt-1`}>
                      {selectedTicket.priority}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Department</Label>
                    <p className="text-sm">{selectedTicket.department}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Category</Label>
                    <p className="text-sm">{selectedTicket.category || 'Not categorized'}</p>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <Label className="text-sm font-medium">Description</Label>
                  <p className="text-sm text-gray-600 mt-1 bg-gray-50 p-3 rounded">{selectedTicket.description}</p>
                </div>

                {/* Comments */}
                <div>
                  <Label className="text-sm font-medium mb-3 block">Comments</Label>
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {ticketComments.map((comment) => (
                      <div key={comment.id} className="bg-gray-50 p-3 rounded">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-medium text-sm">{comment.author_name}</span>
                          <span className="text-xs text-gray-500">
                            {new Date(comment.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700">{comment.content}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Add Comment */}
                <div>
                  <Label className="text-sm font-medium">Add Comment</Label>
                  <div className="flex space-x-2 mt-1">
                    <Textarea
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      placeholder="Add a comment..."
                      rows={3}
                      className="flex-1"
                    />
                    <Button onClick={addComment} disabled={!newComment.trim()}>
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: BarChart3 },
    { path: '/chat', label: 'AI Chat', icon: MessageCircle },
    { path: '/tickets', label: 'Tickets', icon: Ticket },
    { path: '/documents', label: 'Documents', icon: FileText },
  ];

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">ASI OS</span>
            </Link>
          </div>
          
          <div className="flex space-x-8">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-emerald-500 text-emerald-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

// Main App Component
function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <BrowserRouter>
        <Navigation />
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<ChatInterface />} />
            <Route path="/tickets" element={<TicketManagement />} />
            <Route path="/documents" element={<DocumentManagement />} />
          </Routes>
        </main>
        <Toaster />
      </BrowserRouter>
    </div>
  );
}

export default App;