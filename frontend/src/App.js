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
  MoreHorizontal,
  Trash2,
  Check,
  X,
  Shield,
  Building2,
  PiggyBank,
  Briefcase,
  Scale,
  Code2,
  Target,
  FolderOpen
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Department configuration
const DEPARTMENTS = [
  { id: 'Finance', name: 'Finance', icon: PiggyBank, color: 'bg-green-100 text-green-700 border-green-200' },
  { id: 'People and Talent', name: 'People & Talent', icon: Users, color: 'bg-blue-100 text-blue-700 border-blue-200' },
  { id: 'Information Technology', name: 'IT', icon: Code2, color: 'bg-purple-100 text-purple-700 border-purple-200' },
  { id: 'Legal, Ethics and Compliance', name: 'LEC', icon: Scale, color: 'bg-indigo-100 text-indigo-700 border-indigo-200' },
  { id: 'Business Development', name: 'Business Dev', icon: TrendingUp, color: 'bg-orange-100 text-orange-700 border-orange-200' },
  { id: 'Project Management', name: 'Projects', icon: Target, color: 'bg-pink-100 text-pink-700 border-pink-200' },
  { id: 'Other', name: 'Other', icon: FolderOpen, color: 'bg-gray-100 text-gray-700 border-gray-200' }
];

// Structured Response Component
const StructuredResponse = ({ response, documentsReferenced }) => {
  // Parse response if it's a JSON string, or handle as object/string
  let parsedResponse = response;
  
  if (typeof response === 'string') {
    try {
      // Try to parse as JSON first (for structured responses stored as strings)
      parsedResponse = JSON.parse(response);
    } catch (e) {
      // If parsing fails, it's a plain text response
      return (
        <div className="text-sm whitespace-pre-wrap">
          {response}
          {documentsReferenced > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <div className="text-xs text-gray-500 flex items-center">
                <FileText className="w-3 h-3 mr-1" />
                Referenced {documentsReferenced} company document(s)
              </div>
            </div>
          )}
        </div>
      );
    }
  }
  
  // Handle case where parsedResponse is not a structured object
  if (!parsedResponse || typeof parsedResponse !== 'object' || !parsedResponse.summary) {
    return (
      <div className="text-sm whitespace-pre-wrap">
        {JSON.stringify(parsedResponse) || 'No response available'}
        {documentsReferenced > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <div className="text-xs text-gray-500 flex items-center">
              <FileText className="w-3 h-3 mr-1" />
              Referenced {documentsReferenced} company document(s)
            </div>
          </div>
        )}
      </div>
    );
  }
  
  // Use parsedResponse instead of response
  const structuredData = parsedResponse;

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="pb-3 border-b border-gray-200">
        <h4 className="font-medium text-gray-900 mb-2 flex items-center">
          <CheckCircle className="w-4 h-4 mr-2 text-emerald-600" />
          Summary
        </h4>
        <p className="text-sm text-gray-700">{structuredData.summary}</p>
      </div>

      {/* Details Section */}
      {(structuredData.details?.requirements?.length > 0 || 
        structuredData.details?.procedures?.length > 0 || 
        structuredData.details?.exceptions?.length > 0) && (
        <div className="space-y-3">
          {structuredData.details.requirements?.length > 0 && (
            <div>
              <h5 className="font-medium text-gray-800 mb-2 flex items-center text-sm">
                <AlertCircle className="w-3 h-3 mr-1 text-orange-500" />
                Requirements
              </h5>
              <ul className="text-sm text-gray-600 space-y-1">
                {structuredData.details.requirements.map((req, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-emerald-500 mr-2">•</span>
                    {req}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {structuredData.details.procedures?.length > 0 && (
            <div>
              <h5 className="font-medium text-gray-800 mb-2 flex items-center text-sm">
                <PlayCircle className="w-3 h-3 mr-1 text-blue-500" />
                Procedures
              </h5>
              <ol className="text-sm text-gray-600 space-y-1">
                {structuredData.details.procedures.map((proc, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-blue-500 mr-2 font-medium">{idx + 1}.</span>
                    {proc}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {structuredData.details.exceptions?.length > 0 && (
            <div>
              <h5 className="font-medium text-gray-800 mb-2 flex items-center text-sm">
                <AlertTriangle className="w-3 h-3 mr-1 text-yellow-500" />
                Exceptions
              </h5>
              <ul className="text-sm text-gray-600 space-y-1">
                {structuredData.details.exceptions.map((exc, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="text-yellow-500 mr-2">!</span>
                    {exc}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Action Required */}
      {structuredData.action_required && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
          <h5 className="font-medium text-emerald-800 mb-1 flex items-center text-sm">
            <TrendingUp className="w-3 h-3 mr-1" />
            Action Required
          </h5>
          <p className="text-sm text-emerald-700">{structuredData.action_required}</p>
        </div>
      )}

      {/* Contact Info */}
      {structuredData.contact_info && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <h5 className="font-medium text-blue-800 mb-1 flex items-center text-sm">
            <User className="w-3 h-3 mr-1" />
            Contact Information
          </h5>
          <p className="text-sm text-blue-700">{structuredData.contact_info}</p>
        </div>
      )}

      {/* Related Policies */}
      {structuredData.related_policies?.length > 0 && (
        <div>
          <h5 className="font-medium text-gray-800 mb-2 flex items-center text-sm">
            <FileText className="w-3 h-3 mr-1 text-gray-500" />
            Related Policies
          </h5>
          <div className="flex flex-wrap gap-2">
            {structuredData.related_policies.map((policy, idx) => (
              <Badge key={idx} variant="outline" className="text-xs">
                {policy}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Sources */}
      {documentsReferenced > 0 && (
        <div className="pt-3 border-t border-gray-100">
          <div className="text-xs text-gray-500 flex items-center">
            <FileText className="w-3 h-3 mr-1" />
            Referenced {documentsReferenced} company document(s)
            {structuredData.sources && (
              <span className="ml-2">
                ({structuredData.sources.join(', ')})
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

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
          <h1 className="text-3xl font-bold text-gray-900">ASI AiHub Dashboard</h1>
          <p className="text-gray-600 mt-2">AI-Powered Knowledge Management Platform</p>
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

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600" />
            Quick Actions
          </CardTitle>
          <CardDescription>Access key features and workflows</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link to="/chat">
              <Button className="w-full h-20 flex flex-col gap-2 bg-emerald-600 hover:bg-emerald-700">
                <MessageCircle className="w-6 h-6" />
                <span>Ask AI Assistant</span>
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
                <span>Manage Knowledge Base</span>
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

  const fetchDocumentsCount = async () => {
    try {
      const data = await apiCall('GET', '/documents');
      setDocumentsCount(data.length);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const fetchMessages = async (sessionId) => {
    try {
      const data = await apiCall('GET', `/chat/sessions/${sessionId}/messages`);
      // Parse message content if it's JSON string (for structured responses)
      const parsedMessages = data.map(message => {
        if (message.role === 'assistant' && typeof message.content === 'string') {
          try {
            // Try to parse as JSON
            const parsedContent = JSON.parse(message.content);
            if (parsedContent && typeof parsedContent === 'object') {
              return { ...message, content: parsedContent };
            }
          } catch (e) {
            // If parsing fails, keep original content
          }
        }
        return message;
      });
      setMessages(parsedMessages);
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

  const deleteSession = async (sessionId) => {
    try {
      await apiCall('DELETE', `/chat/sessions/${sessionId}`);
      toast({
        title: "Success",
        description: "Conversation deleted successfully",
      });
      
      // If current session was deleted, clear it
      if (currentSession === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
      
      fetchSessions();
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !currentSession) return;

    setLoading(true);
    try {
      const data = await apiCall('POST', '/chat/send', {
        session_id: currentSession,
        message: inputMessage,
        document_ids: [] // Empty array - backend automatically uses all documents
      });

      // Add messages to UI
      const userMsg = {
        role: 'user',
        content: inputMessage,
        timestamp: new Date().toISOString()
      };
      const aiMsg = {
        role: 'assistant',
        content: data.response, // Now contains structured data
        timestamp: new Date().toISOString(),
        documents_referenced: data.documents_referenced,
        response_type: data.response_type
      };

      setMessages(prev => [...prev, userMsg, aiMsg]);
      setInputMessage('');

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

        {/* Knowledge Base Status */}
        <div className="p-4 border-b border-gray-200">
          <Label className="text-sm font-medium text-gray-700 mb-2 block">Knowledge Base</Label>
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-emerald-600" />
              <span className="text-sm text-emerald-700 font-medium">
                {documentsCount} approved documents
              </span>
            </div>
            <p className="text-xs text-emerald-600 mt-1">
              AI searches all approved company policies automatically
            </p>
          </div>
        </div>

        {/* Session History */}
        <div className="flex-1 overflow-y-auto p-4">
          <Label className="text-sm font-medium text-gray-700 mb-3 block">Recent Conversations</Label>
          <div className="space-y-2">
            {sessions.map((session) => (
              <div key={session.id} className="group relative">
                <Button
                  variant={currentSession === session.id ? "default" : "ghost"}
                  className="w-full justify-start text-left p-3 h-auto pr-8"
                  onClick={() => selectSession(session)}
                >
                  <div className="truncate">
                    <div className="font-medium text-sm truncate">{session.title}</div>
                    <div className="text-xs text-gray-500">
                      {session.messages_count} messages
                    </div>
                  </div>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute right-1 top-1 opacity-0 group-hover:opacity-100 h-6 w-6 p-0"
                  onClick={() => deleteSession(session.id)}
                >
                  <Trash2 className="w-3 h-3" />
                </Button>
              </div>
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
                  <h3 className="text-lg font-medium mb-2">Welcome to ASI AiHub AI Assistant</h3>
                  <p className="mb-4">Ask anything about company policies, procedures, or operational guidance.</p>
                  <div className="bg-gray-50 rounded-lg p-4 max-w-md mx-auto">
                    <p className="text-sm font-medium text-gray-700 mb-2">Try asking:</p>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• "What's our annual leave policy?"</li>
                      <li>• "How do I reset my password?"</li>
                      <li>• "What are the expense reporting rules?"</li>
                      <li>• "How do I request time off?"</li>
                    </ul>
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-4xl rounded-lg p-4 ${
                      message.role === 'user' 
                        ? 'bg-emerald-600 text-white' 
                        : 'bg-white border border-gray-200'
                    }`}>
                      {message.role === 'user' ? (
                        <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                      ) : (
                        <StructuredResponse response={message.content} documentsReferenced={message.documents_referenced} />
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-200 p-6">
              <div className="mb-3">
                <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                  <span>Ask anything about company policies and procedures</span>
                  <span className="flex items-center">
                    <Bot className="w-3 h-3 mr-1" />
                    Powered by GPT-5
                  </span>
                </div>
              </div>
              <div className="flex space-x-3">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask about leave policies, IT requirements, expense reporting..."
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
            <div className="text-center max-w-lg">
              <MessageCircle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-xl font-medium mb-2">ASI AiHub AI Assistant</h3>
              <p className="text-gray-600 mb-4">Your intelligent knowledge assistant with access to all approved company policies and procedures.</p>
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-center space-x-2 mb-2">
                  <FileText className="w-4 h-4 text-emerald-600" />
                  <span className="text-sm font-medium text-gray-700">
                    {documentsCount} approved documents ready
                  </span>
                </div>
                <p className="text-xs text-gray-600">
                  Ask questions and get instant answers from your organizational knowledge base
                </p>
              </div>
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

// Enhanced Document Management Component
const DocumentManagement = () => {
  const [documents, setDocuments] = useState([]);
  const [activeTab, setActiveTab] = useState('Finance');
  const [uploading, setUploading] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false); // For demo purposes
  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    fetchDocuments();
  }, [activeTab]);

  const fetchDocuments = async () => {
    try {
      const endpoint = isAdmin ? '/documents/admin' : `/documents?department=${activeTab}&show_all=${isAdmin}`;
      const data = await apiCall('GET', endpoint);
      const filteredDocs = isAdmin ? data : data.filter(doc => doc.department === activeTab);
      setDocuments(filteredDocs);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const handleFileUpload = async (event, department) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('department', department);

      const data = await apiCall('POST', '/documents/upload', formData, true);
      
      toast({
        title: "Success",
        description: `${data.filename} uploaded and pending approval`,
      });
      
      fetchDocuments();
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setUploading(false);
    }
  };

  const approveDocument = async (documentId) => {
    try {
      await apiCall('PUT', `/documents/${documentId}/approve`);
      toast({
        title: "Success",
        description: "Document approved and added to knowledge base",
      });
      fetchDocuments();
    } catch (error) {
      console.error('Error approving document:', error);
    }
  };

  const rejectDocument = async (documentId) => {
    try {
      await apiCall('PUT', `/documents/${documentId}/reject`, { notes: "Not approved for knowledge base" });
      toast({
        title: "Success",
        description: "Document rejected",
      });
      fetchDocuments();
    } catch (error) {
      console.error('Error rejecting document:', error);
    }
  };

  const deleteDocument = async (documentId) => {
    try {
      await apiCall('DELETE', `/documents/${documentId}`);
      toast({
        title: "Success",
        description: "Document deleted successfully",
      });
      fetchDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
    }
  };

  const getStatusBadge = (document) => {
    const status = document.approval_status;
    const colors = {
      'pending_approval': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'approved': 'bg-green-100 text-green-800 border-green-200',
      'rejected': 'bg-red-100 text-red-800 border-red-200'
    };
    
    return (
      <Badge className={colors[status] || colors['pending_approval']}>
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  const getDepartmentIcon = (departmentId) => {
    const dept = DEPARTMENTS.find(d => d.id === departmentId);
    return dept ? dept.icon : FolderOpen;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base Management</h1>
          <p className="text-gray-600 mt-2">Organize and manage approved documents by department</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant={isAdmin ? "default" : "outline"}
            onClick={() => setIsAdmin(!isAdmin)}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            <Shield className="w-4 h-4 mr-2" />
            {isAdmin ? "Admin View" : "Switch to Admin"}
          </Button>
        </div>
      </div>

      {/* Department Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-7 bg-white border-2 border-emerald-200 rounded-lg p-1 shadow-sm">
          {DEPARTMENTS.map((dept) => {
            const Icon = dept.icon;
            return (
              <TabsTrigger 
                key={dept.id} 
                value={dept.id} 
                className="flex items-center justify-center space-x-1 px-2 py-2 rounded-md border-2 border-transparent data-[state=active]:border-emerald-400 data-[state=active]:bg-emerald-50 data-[state=active]:text-emerald-700 hover:bg-gray-50 transition-all duration-200"
              >
                <Icon className="w-4 h-4" />
                <span className="text-xs font-medium">{dept.name}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {DEPARTMENTS.map((dept) => {
          const Icon = dept.icon;
          const deptDocuments = documents.filter(doc => doc.department === dept.id);
          
          return (
            <TabsContent key={dept.id} value={dept.id} className="space-y-4">
              {/* Upload Section */}
              <Card>
                <CardHeader>
                  <CardTitle className={`flex items-center gap-2 ${dept.color}`}>
                    <Icon className="w-5 h-5" />
                    {dept.name} - Upload Documents
                  </CardTitle>
                  <CardDescription>
                    Upload documents for {dept.name}. {isAdmin ? "Admin approval required before adding to knowledge base." : "Documents must be approved before being searchable."}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-emerald-400 transition-colors">
                    <FileUp className="w-10 h-10 mx-auto mb-3 text-gray-400" />
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      {uploading ? 'Uploading...' : `Upload ${dept.name} Documents`}
                    </p>
                    <p className="text-xs text-gray-500 mb-3">
                      Supports PDF, DOCX, and TXT files
                    </p>
                    <input
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={(e) => handleFileUpload(e, dept.id)}
                      disabled={uploading}
                      className="hidden"
                      id={`file-upload-${dept.id}`}
                    />
                    <Label htmlFor={`file-upload-${dept.id}`}>
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
                  <CardTitle>{dept.name} Documents</CardTitle>
                  <CardDescription>
                    {deptDocuments.length} document(s) {isAdmin ? "in this department" : "approved for knowledge base"}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {deptDocuments.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Icon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                      <p>No documents in {dept.name} yet</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {deptDocuments.map((doc) => (
                        <div key={doc.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                          <div className="flex items-center space-x-3">
                            <FileText className="w-8 h-8 text-emerald-600" />
                            <div>
                              <h3 className="font-medium text-gray-900">{doc.original_name}</h3>
                              <p className="text-sm text-gray-500">
                                Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}
                                {doc.uploaded_by && ` by ${doc.uploaded_by}`}
                              </p>
                              {doc.notes && (
                                <p className="text-xs text-gray-400 mt-1">{doc.notes}</p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center space-x-3">
                            <Badge variant="outline">
                              {(doc.file_size / 1024).toFixed(1)} KB
                            </Badge>
                            {getStatusBadge(doc)}
                            {doc.processed && (
                              <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                                {doc.chunks_count} chunks
                              </Badge>
                            )}
                            {isAdmin && (
                              <div className="flex space-x-1">
                                {doc.approval_status === 'pending_approval' && (
                                  <>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => approveDocument(doc.id)}
                                      className="h-8 w-8 p-0"
                                    >
                                      <Check className="w-4 h-4 text-green-600" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => rejectDocument(doc.id)}
                                      className="h-8 w-8 p-0"
                                    >
                                      <X className="w-4 h-4 text-red-600" />
                                    </Button>
                                  </>
                                )}
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => deleteDocument(doc.id)}
                                  className="h-8 w-8 p-0"
                                >
                                  <Trash2 className="w-4 h-4 text-red-600" />
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
};

// Enhanced Ticket Management Component (keeping existing implementation)
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
                  {DEPARTMENTS.map(dept => (
                    <SelectItem key={dept.id} value={dept.id}>{dept.name}</SelectItem>
                  ))}
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
                    {DEPARTMENTS.map(dept => (
                      <SelectItem key={dept.id} value={dept.id}>{dept.name}</SelectItem>
                    ))}
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
    { path: '/chat', label: 'AI Assistant', icon: MessageCircle },
    { path: '/tickets', label: 'Tickets', icon: Ticket },
    { path: '/documents', label: 'Knowledge Base', icon: FileText },
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
              <span className="text-xl font-bold text-gray-900">ASI AiHub</span>
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