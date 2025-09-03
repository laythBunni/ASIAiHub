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
  FolderOpen,
  RefreshCw,
  Save
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
        // Fetch real statistics from existing endpoints
        const [tickets, documents, ragStats] = await Promise.all([
          apiCall('GET', '/boost/tickets').catch(() => []),
          apiCall('GET', '/documents?show_all=true').catch(() => []),
          apiCall('GET', '/documents/rag-stats').catch(() => ({ total_documents: 0, processed_documents: 0 }))
        ]);

        // Calculate real statistics with better error handling
        const totalTickets = Array.isArray(tickets) ? tickets.length : 0;
        const openTickets = Array.isArray(tickets) ? tickets.filter(t => t && t.status === 'open').length : 0;
        const totalDocuments = Array.isArray(documents) ? documents.length : 0;
        const approvedDocuments = Array.isArray(documents) ? documents.filter(d => d && d.approval_status === 'approved').length : 0;
        const overdueTickets = Array.isArray(tickets) ? tickets.filter(t => 
          t && t.due_at && new Date(t.due_at) < new Date() && !['resolved', 'closed'].includes(t.status)
        ).length : 0;

        console.log('Dashboard Stats Debug:', {
          ticketsCount: totalTickets,
          openCount: openTickets,
          documentsCount: totalDocuments,
          approvedCount: approvedDocuments,
          overdueCount: overdueTickets,
          ragStats
        });

        setStats({
          totalTickets,
          openTickets,
          totalDocuments: ragStats?.total_documents || totalDocuments,
          overdue: overdueTickets,
          processed_documents: ragStats?.processed_documents || approvedDocuments
        });
      } catch (error) {
        console.error('Error fetching stats:', error);
        // Set default stats if API calls fail
        setStats({
          totalTickets: 0,
          openTickets: 0,
          totalDocuments: 0,
          overdue: 0,
          processed_documents: 0
        });
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
            <div className="text-2xl font-bold text-emerald-900">{stats.totalTickets}</div>
            <p className="text-xs text-emerald-600 mt-1">All support requests</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-700">Open Tickets</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-900">{stats.openTickets}</div>
            <p className="text-xs text-orange-600 mt-1">Awaiting resolution</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">Documents</CardTitle>
            <FileText className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">{stats.totalDocuments}</div>
            <p className="text-xs text-blue-600 mt-1">Knowledge base files</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-700">Overdue</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-900">{stats.overdue}</div>
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
                <span>Ask Ashur</span>
              </Button>
            </Link>
            <Link to="/boost">
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
            <h2 className="text-xl font-bold text-gray-900">Ashur</h2>
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
                  <h3 className="text-lg font-medium mb-2">Welcome to ASI AiHub Ashur</h3>
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
              <h3 className="text-xl font-medium mb-2">ASI AiHub Ashur</h3>
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
      if (isAdmin) {
        // Admin sees all documents
        const data = await apiCall('GET', '/documents/admin');
        setDocuments(data);
      } else {
        // Regular users see only approved documents for the current tab
        const data = await apiCall('GET', `/documents?department=${activeTab}&approval_status=approved`);
        setDocuments(data);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
      setDocuments([]); // Set empty array on error
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
      formData.append('tags', '');

      const data = await apiCall('POST', '/documents/upload', formData, true);
      
      toast({
        title: "Success",
        description: `${data.filename} uploaded and pending approval`,
      });
      
      // Clear the input
      event.target.value = '';
      
      // Refresh documents
      fetchDocuments();
    } catch (error) {
      console.error('Error uploading file:', error);
      toast({
        title: "Upload Error",
        description: "Failed to upload document. Please try again.",
        variant: "destructive"
      });
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
                className={`flex items-center justify-center space-x-1 px-2 py-2 rounded-md border-2 border-transparent data-[state=active]:${dept.color} hover:bg-gray-50 transition-all duration-200`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-xs font-medium">{dept.name}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>

        {DEPARTMENTS.map((dept) => {
          const Icon = dept.icon;
          const deptDocuments = isAdmin 
            ? documents.filter(doc => doc.department === dept.id)
            : documents; // For regular users, documents are already filtered by department
          
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
                              {doc.department && (
                                <div className="flex items-center mt-1">
                                  <Badge 
                                    variant="outline" 
                                    className={`text-xs ${DEPARTMENTS.find(d => d.id === doc.department)?.color || 'bg-gray-100 text-gray-700 border-gray-200'}`}
                                  >
                                    {DEPARTMENTS.find(d => d.id === doc.department)?.name || doc.department}
                                  </Badge>
                                </div>
                              )}
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

// BOOST Support Ticketing System
const BoostSupport = () => {
  const [tickets, setTickets] = useState([]);
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    support_department: '',
    business_unit_id: ''
  });
  const [currentUser] = useState({
    id: 'default_user',
    name: 'System User',
    email: 'user@company.com',
    boost_role: 'Manager', // Admin, Manager, Agent, User
    business_unit_id: null
  });
  const [showNewTicketModal, setShowNewTicketModal] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showTicketDetail, setShowTicketDetail] = useState(false);
  const [businessUnits, setBusinessUnits] = useState([]);
  const [categories, setCategories] = useState({});
  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    fetchTickets();
    fetchBusinessUnits();
    fetchCategories();
  }, [filters]);

  const fetchTickets = async () => {
    try {
      const queryParams = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== 'all' && value !== 'none') queryParams.append(key, value);
      });
      
      const endpoint = queryParams.toString() ? `/boost/tickets?${queryParams}` : '/boost/tickets';
      const data = await apiCall('GET', endpoint);
      setTickets(data);
    } catch (error) {
      console.error('Error fetching BOOST tickets:', error);
    }
  };

  const fetchBusinessUnits = async () => {
    try {
      const data = await apiCall('GET', '/boost/business-units');
      setBusinessUnits(data);
    } catch (error) {
      console.error('Error fetching business units:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const data = await apiCall('GET', '/boost/categories');
      setCategories(data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  // Enhanced role-based permissions
  const canViewAllTickets = () => {
    return ['Admin', 'Manager'].includes(currentUser.boost_role);
  };

  const canViewDepartmentTickets = () => {
    return ['Agent', 'Manager', 'Admin'].includes(currentUser.boost_role);
  };

  const canCloseTickets = () => {
    return ['Manager', 'Admin'].includes(currentUser.boost_role);
  };

  // Filter tickets by column with enhanced permissions
  const getToDoTickets = () => {
    let filteredTickets = [];
    
    if (currentUser.boost_role === 'User') {
      // End users: only tickets where they are mentioned or need to respond
      filteredTickets = tickets.filter(ticket => 
        (ticket.requester_id === currentUser.id && ticket.status === 'waiting_customer') ||
        (ticket.owner_id === currentUser.id)
      );
    } else if (currentUser.boost_role === 'Agent') {
      // Agents: assigned tickets in their department
      filteredTickets = tickets.filter(ticket => 
        ticket.owner_id === currentUser.id && 
        ['open', 'in_progress', 'waiting_customer'].includes(ticket.status)
      );
    } else {
      // Managers/Admins: all assigned tickets
      filteredTickets = tickets.filter(ticket => 
        ticket.owner_id === currentUser.id && 
        ['open', 'in_progress', 'waiting_customer'].includes(ticket.status)
      );
    }
    
    return filteredTickets;
  };

  const getCreatedByYouTickets = () => {
    return tickets.filter(ticket => ticket.requester_id === currentUser.id);
  };

  const getAllTickets = () => {
    if (currentUser.boost_role === 'Admin' || currentUser.boost_role === 'Manager') {
      return tickets; // Full visibility
    } else if (currentUser.boost_role === 'Agent') {
      // Agents: only tickets in their department
      return tickets.filter(ticket => 
        ticket.support_department === currentUser.department ||
        ticket.requester_id === currentUser.id ||
        ticket.owner_id === currentUser.id
      );
    } else {
      // End users: only their own tickets
      return tickets.filter(ticket => ticket.requester_id === currentUser.id);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      open: 'bg-orange-100 text-orange-700 border-orange-200',
      in_progress: 'bg-blue-100 text-blue-700 border-blue-200',
      waiting_customer: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      on_hold: 'bg-purple-100 text-purple-700 border-purple-200',
      escalated: 'bg-red-100 text-red-700 border-red-200',
      resolved: 'bg-green-100 text-green-700 border-green-200',
      closed: 'bg-gray-100 text-gray-700 border-gray-200'
    };
    return colors[status] || colors.open;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'bg-gray-100 text-gray-700',
      medium: 'bg-blue-100 text-blue-700',
      high: 'bg-orange-100 text-orange-700',
      urgent: 'bg-red-100 text-red-700' // Critical
    };
    return colors[priority] || colors.medium;
  };

  const getDepartmentColor = (department) => {
    const colors = {
      'OS Support': 'bg-green-100 text-green-700',
      'Finance': 'bg-blue-100 text-blue-700',
      'HR/P&T': 'bg-purple-100 text-purple-700',
      'IT': 'bg-indigo-100 text-indigo-700',
      'DevOps': 'bg-red-100 text-red-700'
    };
    return colors[department] || colors['OS Support'];
  };

  const openTicketDetail = (ticket) => {
    setSelectedTicket(ticket);
    setShowTicketDetail(true);
  };

  const TicketRow = ({ ticket, showQuickActions = true }) => (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1" onClick={() => openTicketDetail(ticket)}>
          <h3 className="font-medium text-gray-900 text-sm mb-2 line-clamp-2">
            {ticket.subject}
          </h3>
          <div className="flex flex-wrap gap-1 mb-2">
            <Badge className={`text-xs ${getStatusColor(ticket.status)}`}>
              {ticket.status.toUpperCase().replace('_', ' ')}
            </Badge>
            <Badge className={`text-xs ${getDepartmentColor(ticket.support_department)}`}>
              {ticket.support_department}
            </Badge>
            <Badge className={`text-xs ${getPriorityColor(ticket.priority)}`}>
              {ticket.priority.toUpperCase()}
            </Badge>
          </div>
          <p className="text-xs text-gray-500">
            Created {new Date(ticket.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>
      
      {showQuickActions && (
        <div className="flex space-x-1 pt-2 border-t border-gray-100">
          <Button size="sm" variant="outline" onClick={() => openTicketDetail(ticket)}>
            <Eye className="w-3 h-3 mr-1" />
            View
          </Button>
          <Button size="sm" variant="outline" onClick={() => openTicketDetail(ticket)}>
            <MessageSquare className="w-3 h-3 mr-1" />
            Comment
          </Button>
          <Button size="sm" variant="outline" onClick={() => {
            // TODO: Implement file upload functionality
            alert('File upload functionality will be implemented in Phase 2');
          }}>
            <Upload className="w-3 h-3 mr-1" />
            Attach
          </Button>
          {ticket.status === 'waiting_customer' && ticket.requester_id === currentUser.id && (
            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700">
              <CheckCircle className="w-3 h-3 mr-1" />
              Done
            </Button>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">BOOST Support</h1>
          <p className="text-gray-600 mt-2">Comprehensive support ticketing system</p>
        </div>
        <Button onClick={() => setShowNewTicketModal(true)} className="bg-emerald-600 hover:bg-emerald-700">
          <Plus className="w-4 h-4 mr-2" />
          New Ticket
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Input
              placeholder="Search tickets..."
              value={filters.search}
              onChange={(e) => setFilters({...filters, search: e.target.value})}
              className="w-full"
            />
            <Select value={filters.status} onValueChange={(value) => setFilters({...filters, status: value})}>
              <SelectTrigger>
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="open">New</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="waiting_customer">Waiting on User</SelectItem>
                <SelectItem value="on_hold">On Hold</SelectItem>
                <SelectItem value="escalated">Escalated</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                {(currentUser.boost_role === 'Manager' || currentUser.boost_role === 'Admin') && (
                  <SelectItem value="closed">Closed</SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filters.support_department} onValueChange={(value) => setFilters({...filters, support_department: value})}>
              <SelectTrigger>
                <SelectValue placeholder="All departments" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All departments</SelectItem>
                <SelectItem value="OS Support">OS Support</SelectItem>
                <SelectItem value="Finance">Finance</SelectItem>
                <SelectItem value="HR/P&T">HR/P&T</SelectItem>
                <SelectItem value="IT">IT</SelectItem>
                <SelectItem value="DevOps">DevOps</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filters.business_unit_id} onValueChange={(value) => setFilters({...filters, business_unit_id: value})}>
              <SelectTrigger>
                <SelectValue placeholder="All business units" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All business units</SelectItem>
                {businessUnits.map(unit => (
                  <SelectItem key={unit.id} value={unit.id}>{unit.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 3-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Column 1: Your tickets – To do */}
        <Card className="h-fit">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="w-5 h-5 text-orange-600" />
              Your tickets – To do
            </CardTitle>
            <CardDescription>
              {getToDoTickets().length} ticket(s) requiring your action
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {getToDoTickets().length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">All caught up!</p>
              </div>
            ) : (
              getToDoTickets().map(ticket => (
                <TicketRow key={ticket.id} ticket={ticket} />
              ))
            )}
          </CardContent>
        </Card>

        {/* Column 2: Your tickets – Created by you */}
        <Card className="h-fit">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <User className="w-5 h-5 text-blue-600" />
              Your tickets – Created by you
            </CardTitle>
            <CardDescription>
              {getCreatedByYouTickets().length} ticket(s) you've submitted
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {getCreatedByYouTickets().length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Ticket className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No tickets created yet</p>
              </div>
            ) : (
              getCreatedByYouTickets().map(ticket => (
                <TicketRow key={ticket.id} ticket={ticket} />
              ))
            )}
          </CardContent>
        </Card>

        {/* Column 3: Role-based ticket view */}
        <Card className="h-fit">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              {currentUser.boost_role === 'Admin' || currentUser.boost_role === 'Manager' ? (
                <>
                  <Shield className="w-5 h-5 text-emerald-600" />
                  All tickets ({currentUser.boost_role})
                </>
              ) : currentUser.boost_role === 'Agent' ? (
                <>
                  <Building2 className="w-5 h-5 text-purple-600" />
                  Department tickets
                </>
              ) : (
                <>
                  <Eye className="w-5 h-5 text-gray-600" />
                  Your tickets
                </>
              )}
            </CardTitle>
            <CardDescription>
              {currentUser.boost_role === 'Admin' || currentUser.boost_role === 'Manager' 
                ? `${getAllTickets().length} total ticket(s) in system`
                : currentUser.boost_role === 'Agent'
                ? `${getAllTickets().length} ticket(s) in ${currentUser.department || 'your department'}`
                : `${getAllTickets().length} ticket(s) you can view`
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {getAllTickets().length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Ticket className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">
                  {currentUser.boost_role === 'User' ? 'No tickets found' : 'No tickets in view'}
                </p>
              </div>
            ) : (
              getAllTickets().slice(0, 10).map(ticket => (
                <TicketRow key={ticket.id} ticket={ticket} showQuickActions={true} />
              ))
            )}
            {getAllTickets().length > 10 && (
              <div className="text-center pt-2">
                <Button variant="outline" size="sm">
                  View all {getAllTickets().length} tickets
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* New Ticket Modal */}
      <BoostNewTicketModal 
        isOpen={showNewTicketModal}
        onClose={() => setShowNewTicketModal(false)}
        onSubmit={() => {
          setShowNewTicketModal(false);
          fetchTickets();
        }}
        businessUnits={businessUnits}
        categories={categories}
        currentUser={currentUser}
      />

      {/* Ticket Detail Modal */}
      <BoostTicketDetailModal
        isOpen={showTicketDetail}
        onClose={() => setShowTicketDetail(false)}
        ticket={selectedTicket}
        currentUser={currentUser}
        onUpdate={() => {
          fetchTickets();
        }}
      />
    </div>
  );
};

// BOOST New Ticket Modal Component
const BoostNewTicketModal = ({ isOpen, onClose, onSubmit, businessUnits, categories, currentUser }) => {
  const [formData, setFormData] = useState({
    support_department: '',
    category: '',
    subcategory: '',
    subject: '',
    description: '',
    classification: '',
    priority: '',
    justification: '',
    business_unit_id: currentUser.business_unit_id || '',
    channel: 'Hub'
  });
  const [availableCategories, setAvailableCategories] = useState({});
  const [availableSubcategories, setAvailableSubcategories] = useState([]);
  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    if (formData.support_department && categories[formData.support_department]) {
      setAvailableCategories(categories[formData.support_department]);
      setFormData(prev => ({ ...prev, category: '', subcategory: '' }));
    }
  }, [formData.support_department, categories]);

  useEffect(() => {
    if (formData.category && availableCategories[formData.category]) {
      setAvailableSubcategories(availableCategories[formData.category]);
      setFormData(prev => ({ ...prev, subcategory: '' }));
    }
  }, [formData.category, availableCategories]);

  const handleSubmit = async () => {
    try {
      // Validation
      if (!formData.support_department || !formData.category || !formData.subcategory || 
          !formData.subject || !formData.description || !formData.classification || !formData.priority) {
        toast({
          title: "Validation Error",
          description: "Please fill in all required fields",
          variant: "destructive"
        });
        return;
      }

      if (formData.priority === 'urgent' && !formData.justification.trim()) {
        toast({
          title: "Validation Error", 
          description: "Critical priority requires justification",
          variant: "destructive"
        });
        return;
      }

      const ticketData = {
        ...formData,
        requester_name: currentUser.name,
        requester_email: currentUser.email
      };

      await apiCall('POST', '/boost/tickets', ticketData);
      
      toast({
        title: "Success",
        description: "Ticket created successfully",
      });
      
      onSubmit();
      
      // Reset form
      setFormData({
        support_department: '',
        category: '',
        subcategory: '',
        subject: '',
        description: '',
        classification: '',
        priority: '',
        justification: '',
        business_unit_id: currentUser.business_unit_id || '',
        channel: 'Hub'
      });
    } catch (error) {
      console.error('Error creating ticket:', error);
    }
  };

  const getPriorityTargets = (priority) => {
    const targets = {
      low: 'Target: 2 business days response',
      medium: 'Target: 1 business day response', 
      high: 'Target: 4 hours response',
      urgent: 'Target: 15 minutes first response, 1 hour resolution'
    };
    return targets[priority] || '';
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>New Support Ticket</DialogTitle>
          <DialogDescription>Create a new BOOST support request</DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Support Department */}
          <div>
            <Label htmlFor="support_department">Support Department *</Label>
            <Select value={formData.support_department} onValueChange={(value) => setFormData({...formData, support_department: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Select department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="OS Support">OS Support</SelectItem>
                <SelectItem value="Finance">Finance</SelectItem>
                <SelectItem value="HR/P&T">HR/P&T</SelectItem>
                <SelectItem value="IT">IT</SelectItem>
                <SelectItem value="DevOps">DevOps</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Category */}
          <div>
            <Label htmlFor="category">Category *</Label>
            <Select value={formData.category} onValueChange={(value) => setFormData({...formData, category: value})} disabled={!formData.support_department}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {Object.keys(availableCategories).map(cat => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Subcategory */}
          <div>
            <Label htmlFor="subcategory">Subcategory *</Label>
            <Select value={formData.subcategory} onValueChange={(value) => setFormData({...formData, subcategory: value})} disabled={!formData.category}>
              <SelectTrigger>
                <SelectValue placeholder="Select subcategory" />
              </SelectTrigger>
              <SelectContent>
                {availableSubcategories.map(subcat => (
                  <SelectItem key={subcat} value={subcat}>{subcat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Subject */}
          <div>
            <Label htmlFor="subject">Subject *</Label>
            <Input
              id="subject"
              value={formData.subject}
              onChange={(e) => setFormData({...formData, subject: e.target.value})}
              placeholder="Brief description of the issue"
            />
            {formData.support_department && formData.category && (
              <p className="text-xs text-gray-500 mt-1">
                Will be prefixed as: "{formData.support_department}: {formData.category} – {formData.subject}"
              </p>
            )}
          </div>

          {/* Description */}
          <div>
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Please include what happened, when it started, any error messages, steps you tried"
              rows={4}
            />
          </div>

          {/* Classification */}
          <div>
            <Label htmlFor="classification">Classification *</Label>
            <Select value={formData.classification} onValueChange={(value) => setFormData({...formData, classification: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Select classification" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Incident">Incident</SelectItem>
                <SelectItem value="Bug">Bug</SelectItem>
                <SelectItem value="ServiceRequest">Service Request</SelectItem>
                <SelectItem value="ChangeRequest">Change Request</SelectItem>
                <SelectItem value="Implementation">Implementation/Enhancement</SelectItem>
                <SelectItem value="HowToQuery">How-To/Query</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Priority */}
          <div>
            <Label htmlFor="priority">Priority *</Label>
            <Select value={formData.priority} onValueChange={(value) => setFormData({...formData, priority: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Select priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low - General "how-to"</SelectItem>
                <SelectItem value="medium">Medium - Minor blocker w/ workaround</SelectItem>
                <SelectItem value="high">High - Payroll/PO blockers, MFA lockouts</SelectItem>
                <SelectItem value="urgent">Critical - Outage, payroll cut-off, compliance breach</SelectItem>
              </SelectContent>
            </Select>
            {formData.priority && (
              <p className="text-xs text-emerald-600 mt-1">
                {getPriorityTargets(formData.priority)}
              </p>
            )}
          </div>

          {/* Critical Justification */}
          {formData.priority === 'urgent' && (
            <div>
              <Label htmlFor="justification">Critical Justification *</Label>
              <Textarea
                id="justification"
                value={formData.justification}
                onChange={(e) => setFormData({...formData, justification: e.target.value})}
                placeholder="Please explain why this is critical priority"
                rows={3}
              />
            </div>
          )}

          {/* Business Unit */}
          <div>
            <Label htmlFor="business_unit_id">Business Unit</Label>
            <Select value={formData.business_unit_id} onValueChange={(value) => setFormData({...formData, business_unit_id: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Select business unit" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {businessUnits.map(unit => (
                  <SelectItem key={unit.id} value={unit.id}>{unit.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit} className="bg-emerald-600 hover:bg-emerald-700">
              Create Ticket
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Enhanced BOOST Ticket Detail Modal with Audit Trail & Quick Actions
const BoostTicketDetailModal = ({ isOpen, onClose, ticket, currentUser, onUpdate }) => {
  const [comments, setComments] = useState([]);
  const [auditTrail, setAuditTrail] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [attachments, setAttachments] = useState([]);
  
  // Quick Actions state
  const [quickStatus, setQuickStatus] = useState('');
  const [quickPriority, setQuickPriority] = useState('');
  const [quickAssignee, setQuickAssignee] = useState('');
  const [availableAgents, setAvailableAgents] = useState([]);

  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    if (ticket && isOpen) {
      fetchComments();
      fetchAuditTrail();
      fetchAttachments();
      fetchAvailableAgents();
      // Initialize quick actions with current ticket values
      setQuickStatus(ticket.status);
      setQuickPriority(ticket.priority);
      setQuickAssignee(ticket.owner_id || 'unassigned');
    }
  }, [ticket, isOpen]);

  const fetchComments = async () => {
    if (!ticket) return;
    try {
      const data = await apiCall('GET', `/boost/tickets/${ticket.id}/comments`);
      setComments(data);
    } catch (error) {
      console.error('Error fetching comments:', error);
    }
  };

  const fetchAuditTrail = async () => {
    if (!ticket) return;
    try {
      // Try to get real audit trail from backend first
      let trail = [];
      
      try {
        const auditData = await apiCall('GET', `/boost/tickets/${ticket.id}/audit`);
        trail = auditData || [];
      } catch (error) {
        // If no backend audit endpoint, create comprehensive trail from available data
        console.log('No audit endpoint available, creating trail from ticket data');
      }

      // If no backend trail exists, create comprehensive trail from ticket and comments data
      if (trail.length === 0) {
        // Base ticket creation
        trail.push({
          id: 1,
          action: 'created',
          description: `Ticket created by ${ticket.requester_name}`,
          user_name: ticket.requester_name,
          timestamp: ticket.created_at,
          details: `Priority: ${ticket.priority.toUpperCase()}, Department: ${ticket.support_department}, Category: ${ticket.category}`
        });

        // Assignment tracking
        if (ticket.owner_name) {
          trail.push({
            id: 2,
            action: 'assigned',
            description: `Assigned to ${ticket.owner_name}`,
            user_name: 'System',
            timestamp: ticket.updated_at,
            details: `Owner: ${ticket.owner_name} (${ticket.support_department})`
          });
        }

        // Status change tracking
        if (ticket.status !== 'open') {
          trail.push({
            id: 3,
            action: 'status_changed',
            description: `Status changed to ${ticket.status.replace('_', ' ')}`,
            user_name: ticket.owner_name || 'System',
            timestamp: ticket.updated_at,
            details: `Previous: Open → Current: ${ticket.status.toUpperCase().replace('_', ' ')}`
          });
        }

        // Priority changes (if different from default)
        if (ticket.priority !== 'medium') {
          trail.push({
            id: 4,
            action: 'priority_changed',
            description: `Priority set to ${ticket.priority.toUpperCase()}`,
            user_name: ticket.owner_name || ticket.requester_name,
            timestamp: ticket.updated_at,
            details: `Priority level: ${ticket.priority.toUpperCase()}`
          });
        }

        // Add comment entries from comments data
        comments.forEach((comment, index) => {
          trail.push({
            id: 100 + index,
            action: 'comment_added',
            description: comment.is_internal ? 'Internal comment added' : 'Comment added',
            user_name: comment.author_name,
            timestamp: comment.created_at,
            details: comment.body.substring(0, 100) + (comment.body.length > 100 ? '...' : '')
          });
        });

        // Add attachment entries (if any)
        attachments.forEach((attachment, index) => {
          trail.push({
            id: 200 + index,
            action: 'attachment_added',
            description: `File attached: ${attachment.original_name}`,
            user_name: attachment.uploaded_by || 'System',
            timestamp: attachment.uploaded_at || ticket.updated_at,
            details: `File: ${attachment.original_name} (${attachment.file_size || 'Unknown size'})`
          });
        });

        // SLA tracking
        if (ticket.due_at && new Date(ticket.due_at) < new Date() && !['resolved', 'closed'].includes(ticket.status)) {
          trail.push({
            id: 300,
            action: 'sla_breach',
            description: 'SLA deadline exceeded',
            user_name: 'System',
            timestamp: ticket.due_at,
            details: `Due date: ${new Date(ticket.due_at).toLocaleString()}`
          });
        }
      }

      // Sort by timestamp (newest first)
      setAuditTrail(trail.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
    } catch (error) {
      console.error('Error creating audit trail:', error);
      setAuditTrail([]);
    }
  };

  const fetchAttachments = async () => {
    if (!ticket) return;
    try {
      // Try to fetch attachments from backend
      const attachments = await apiCall('GET', `/boost/tickets/${ticket.id}/attachments`);
      setAttachments(attachments || []);
    } catch (error) {
      console.error('Error fetching attachments:', error);
      setAttachments([]);
    }
  };

  const handleFileUpload = async (files) => {
    if (!ticket || files.length === 0) return;

    try {
      const uploadPromises = Array.from(files).map(async (file) => {
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
          toast({
            title: "File too large",
            description: `${file.name} exceeds 10MB limit`,
            variant: "destructive"
          });
          return null;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('ticket_id', ticket.id);
        formData.append('uploaded_by', currentUser.name);

        try {
          const response = await fetch(`${API}/boost/tickets/${ticket.id}/attachments`, {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
          }

          return await response.json();
        } catch (error) {
          toast({
            title: "Upload failed",
            description: `Failed to upload ${file.name}: ${error.message}`,
            variant: "destructive"
          });
          return null;
        }
      });

      const results = await Promise.all(uploadPromises);
      const successful = results.filter(r => r !== null);
      
      if (successful.length > 0) {
        toast({
          title: "Upload successful",
          description: `${successful.length} file(s) uploaded successfully`,
        });
        
        // Add audit trail entry
        await apiCall('POST', `/boost/tickets/${ticket.id}/comments`, {
          body: `${successful.length} file(s) attached: ${successful.map(f => f.original_name).join(', ')}`,
          is_internal: false,
          author_name: currentUser.name
        });
        
        fetchAttachments();
        fetchComments();
        fetchAuditTrail();
      }
    } catch (error) {
      console.error('Error uploading files:', error);
      toast({
        title: "Upload error",
        description: "Failed to process file uploads",
        variant: "destructive"
      });
    }
  };

  const fetchAvailableAgents = async () => {
    try {
      const users = await apiCall('GET', '/boost/users');
      const agents = users.filter(user => 
        ['Agent', 'Manager', 'Admin'].includes(user.boost_role)
      );
      setAvailableAgents(agents);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const handleQuickAction = async () => {
    try {
      const updates = {};
      let changeDescription = [];

      if (quickStatus !== ticket.status) {
        updates.status = quickStatus;
        changeDescription.push(`Status: ${quickStatus.replace('_', ' ')}`);
      }
      if (quickPriority !== ticket.priority) {
        updates.priority = quickPriority;
        changeDescription.push(`Priority: ${quickPriority}`);
      }
      if (quickAssignee !== (ticket.owner_id || 'unassigned')) {
        updates.owner_id = quickAssignee === 'unassigned' ? null : quickAssignee;
        const agent = availableAgents.find(a => a.id === quickAssignee);
        updates.owner_name = agent ? agent.name : null;
        changeDescription.push(`Assignee: ${agent?.name || 'Unassigned'}`);
      }

      if (Object.keys(updates).length > 0) {
        await apiCall('PUT', `/boost/tickets/${ticket.id}`, updates);
        
        // Add audit trail entry
        await apiCall('POST', `/boost/tickets/${ticket.id}/comments`, {
          body: `Quick action applied: ${changeDescription.join(', ')}`,
          is_internal: true,
          author_name: currentUser.name
        });

        toast({
          title: "Success",
          description: "Ticket updated successfully",
        });

        fetchComments();
        fetchAuditTrail();
        onUpdate();
      }
    } catch (error) {
      console.error('Error updating ticket:', error);
      toast({
        title: "Error",
        description: "Failed to update ticket",
        variant: "destructive"
      });
    }
  };

  const canUseQuickActions = () => {
    return ['Manager', 'Admin'].includes(currentUser.boost_role);
  };

  const canCloseTicket = () => {
    return ['Manager', 'Admin'].includes(currentUser.boost_role);
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'created': return <Plus className="w-4 h-4 text-green-600" />;
      case 'assigned': return <User className="w-4 h-4 text-blue-600" />;
      case 'status_changed': return <RefreshCw className="w-4 h-4 text-orange-600" />;
      case 'priority_changed': return <AlertTriangle className="w-4 h-4 text-purple-600" />;
      case 'comment_added': return <MessageSquare className="w-4 h-4 text-gray-600" />;
      case 'attachment_added': return <Upload className="w-4 h-4 text-emerald-600" />;
      case 'sla_breach': return <AlertCircle className="w-4 h-4 text-red-600" />;
      case 'resolved': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'closed': return <Target className="w-4 h-4 text-gray-600" />;
      default: return <Clock className="w-4 h-4 text-gray-600" />;
    }
  };

  if (!ticket) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[1200px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span className="truncate">{ticket.subject}</span>
            <Badge variant="outline">{ticket.ticket_number}</Badge>
          </DialogTitle>
          <DialogDescription>
            Created {new Date(ticket.created_at).toLocaleDateString()} by {ticket.requester_name}
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Ticket Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Ticket Information */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Ticket Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium">Status</Label>
                    <Badge className={`mt-1 ${ticket.status === 'open' ? 'bg-orange-100 text-orange-700' : 
                      ticket.status === 'resolved' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                      {ticket.status.toUpperCase().replace('_', ' ')}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Priority</Label>
                    <Badge className={`mt-1 ${ticket.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                      ticket.priority === 'high' ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'}`}>
                      {ticket.priority.toUpperCase()}
                    </Badge>
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium">Description</Label>
                  <div className="bg-gray-50 p-3 rounded mt-1 text-sm">
                    {ticket.description}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><strong>Department:</strong> {ticket.support_department}</div>
                  <div><strong>Category:</strong> {ticket.category}</div>
                  <div><strong>Subcategory:</strong> {ticket.subcategory}</div>
                  <div><strong>Classification:</strong> {ticket.classification}</div>
                  <div><strong>Business Unit:</strong> {ticket.business_unit_name || 'None'}</div>
                  <div><strong>Owner:</strong> {ticket.owner_name || 'Unassigned'}</div>
                  <div><strong>Due:</strong> {ticket.due_at ? new Date(ticket.due_at).toLocaleString() : 'Not set'}</div>
                  <div><strong>Created:</strong> {new Date(ticket.created_at).toLocaleString()}</div>
                </div>
              </CardContent>
            </Card>

            {/* Attachments */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Attachments</CardTitle>
              </CardHeader>
              <CardContent>
                <div 
                  className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-emerald-400 transition-colors"
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.currentTarget.classList.add('border-emerald-400', 'bg-emerald-50');
                  }}
                  onDragLeave={(e) => {
                    e.preventDefault();
                    e.currentTarget.classList.remove('border-emerald-400', 'bg-emerald-50');
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.currentTarget.classList.remove('border-emerald-400', 'bg-emerald-50');
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                      handleFileUpload(files);
                    }
                  }}
                >
                  <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-500 mb-2">Drop files here or click to upload</p>
                  <input
                    type="file"
                    multiple
                    className="hidden"
                    id="file-upload"
                    accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                    onChange={(e) => {
                      if (e.target.files.length > 0) {
                        handleFileUpload(e.target.files);
                        e.target.value = ''; // Reset input
                      }
                    }}
                  />
                  <Label htmlFor="file-upload">
                    <Button size="sm" variant="outline" asChild>
                      <span>
                        <Upload className="w-4 h-4 mr-2" />
                        Choose Files
                      </span>
                    </Button>
                  </Label>
                  <p className="text-xs text-gray-400 mt-2">PDF, DOC, DOCX, TXT, JPG, PNG (Max 10MB each)</p>
                </div>
                {attachments.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {attachments.map(attachment => (
                      <div key={attachment.id} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                        <span className="text-sm">{attachment.original_name}</span>
                        <Button size="sm" variant="outline">Download</Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Comments */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Comments</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {comments.map(comment => (
                    <div key={comment.id} className={`p-3 rounded text-sm ${
                      comment.is_internal ? 'bg-yellow-50 border-l-4 border-yellow-400' : 'bg-gray-50'
                    }`}>
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium">{comment.author_name}</span>
                        <div className="flex items-center space-x-2">
                          {comment.is_internal && (
                            <Badge variant="outline" className="text-xs">Internal</Badge>
                          )}
                          <span className="text-xs text-gray-500">
                            {new Date(comment.created_at).toLocaleString()}
                          </span>
                        </div>
                      </div>
                      <p>{comment.body}</p>
                    </div>
                  ))}
                </div>

                {/* Add Comment */}
                <div className="border-t pt-4">
                  <div className="space-y-2">
                    {(currentUser.boost_role === 'Agent' || currentUser.boost_role === 'Manager' || currentUser.boost_role === 'Admin') && (
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="internal"
                          checked={isInternal}
                          onChange={(e) => setIsInternal(e.target.checked)}
                        />
                        <Label htmlFor="internal" className="text-sm">Internal comment (staff only)</Label>
                      </div>
                    )}
                    <div className="flex space-x-2">
                      <Textarea
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Add a comment..."
                        rows={3}
                        className="flex-1"
                      />
                      <Button 
                        onClick={async () => {
                          if (newComment.trim()) {
                            try {
                              await apiCall('POST', `/boost/tickets/${ticket.id}/comments`, {
                                body: newComment,
                                is_internal: isInternal,
                                author_name: currentUser.name
                              });
                              setNewComment('');
                              setIsInternal(false);
                              fetchComments();
                              fetchAuditTrail();
                            } catch (error) {
                              console.error('Error adding comment:', error);
                            }
                          }
                        }}
                        disabled={!newComment.trim()}
                      >
                        <Send className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Activity/Audit Trail */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Activity</CardTitle>
                <CardDescription>Complete audit trail of all actions taken on this ticket</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {auditTrail.map(entry => (
                    <div key={entry.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
                      {getActionIcon(entry.action)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{entry.description}</p>
                        <p className="text-xs text-gray-500">{entry.details}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {entry.user_name} • {new Date(entry.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Admin Quick Actions */}
          <div className="space-y-6">
            {canUseQuickActions() && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Admin Quick Actions</CardTitle>
                  <CardDescription>Update key ticket properties quickly</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium">Status</Label>
                    <Select value={quickStatus} onValueChange={setQuickStatus}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="open">New</SelectItem>
                        <SelectItem value="in_progress">In Progress</SelectItem>
                        <SelectItem value="waiting_customer">Waiting on User</SelectItem>
                        <SelectItem value="on_hold">On Hold</SelectItem>
                        <SelectItem value="escalated">Escalated</SelectItem>
                        <SelectItem value="resolved">Resolved</SelectItem>
                        {canCloseTicket() && (
                          <SelectItem value="closed">Closed</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Priority</Label>
                    <Select value={quickPriority} onValueChange={setQuickPriority}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-sm font-medium">Assignee</Label>
                    <Select value={quickAssignee} onValueChange={setQuickAssignee}>
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select assignee" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="unassigned">Unassigned</SelectItem>
                        {availableAgents.map(agent => (
                          <SelectItem key={agent.id} value={agent.id}>
                            {agent.name} ({agent.boost_role}) - {agent.department}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <Button 
                    onClick={handleQuickAction}
                    className="w-full bg-emerald-600 hover:bg-emerald-700"
                    disabled={
                      quickStatus === ticket.status && 
                      quickPriority === ticket.priority && 
                      quickAssignee === (ticket.owner_id || 'unassigned')
                    }
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Ticket Summary */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span>Ticket ID:</span>
                  <span className="font-medium">{ticket.ticket_number}</span>
                </div>
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last Updated:</span>
                  <span>{new Date(ticket.updated_at).toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Comments:</span>
                  <span>{comments.length}</span>
                </div>
                <div className="flex justify-between">
                  <span>Attachments:</span>
                  <span>{attachments.length}</span>
                </div>
                {ticket.due_at && (
                  <div className="flex justify-between">
                    <span>SLA Due:</span>
                    <span className={new Date(ticket.due_at) < new Date() ? 'text-red-600 font-medium' : ''}>
                      {new Date(ticket.due_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </DialogContent>
    </Dialog>
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
        if (value && value !== 'all' && value !== 'none') queryParams.append(key, value);
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
                  <SelectItem value="all">All statuses</SelectItem>
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
                  <SelectItem value="all">All priorities</SelectItem>
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
                  <SelectItem value="all">All departments</SelectItem>
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
    { path: '/chat', label: 'Ashur your ultimate assistant!', icon: MessageCircle },
    { path: '/boost', label: 'BOOST Support', icon: Ticket },
    { path: '/tickets', label: 'Legacy Tickets', icon: Settings },
    { path: '/documents', label: 'Knowledge Base', icon: FileText },
    { path: '/admin', label: 'Admin', icon: Shield },
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

// BOOST Admin Dashboard Component
const BoostAdmin = () => {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [businessUnits, setBusinessUnits] = useState([]);
  const [showNewUserModal, setShowNewUserModal] = useState(false);
  const [showNewUnitModal, setShowNewUnitModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editingUnit, setEditingUnit] = useState(null);
  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    fetchUsers();
    fetchBusinessUnits();
  }, []);

  const createTestUsers = async () => {
    const testUsers = [
      {
        name: 'Admin User',
        email: 'admin@company.test',
        boost_role: 'Admin',
        department: 'OS Support'
      },
      {
        name: 'Finance Manager',
        email: 'manager@company.test',
        boost_role: 'Manager',
        department: 'Finance'
      },
      {
        name: 'Finance Agent',
        email: 'finance.agent@company.test',
        boost_role: 'Agent',
        department: 'Finance'
      },
      {
        name: 'HR Agent',
        email: 'hr.agent@company.test',
        boost_role: 'Agent',
        department: 'HR/P&T'
      },
      {
        name: 'IT Agent',
        email: 'it.agent@company.test',
        boost_role: 'Agent',
        department: 'IT'
      },
      {
        name: 'DevOps Agent',
        email: 'devops.agent@company.test',
        boost_role: 'Agent',
        department: 'DevOps'
      },
      {
        name: 'End User One',
        email: 'user.one@company.test',
        boost_role: 'User',
        department: null
      },
      {
        name: 'End User Two',
        email: 'user.two@company.test',
        boost_role: 'User',
        department: null
      }
    ];

    try {
      let created = 0;
      for (const user of testUsers) {
        try {
          await apiCall('POST', '/boost/users', user);
          created++;
        } catch (error) {
          // User might already exist, skip
        }
      }
      
      toast({
        title: "Success",
        description: `Created ${created} test user accounts`,
      });
      
      fetchUsers();
    } catch (error) {
      console.error('Error creating test users:', error);
      toast({
        title: "Error",
        description: "Failed to create test users",
        variant: "destructive"
      });
    }
  };

  const createTestBusinessUnits = async () => {
    const testUnits = [
      {
        name: 'Africa Division',
        code: 'AFR001',
        type: 'Geography',
        status: 'Active',
        description: 'African regional operations'
      },
      {
        name: 'Asia Pacific',
        code: 'APAC001',
        type: 'Geography', 
        status: 'Active',
        description: 'Asia Pacific regional operations'
      },
      {
        name: 'IT Department',
        code: 'IT-DEPT',
        type: 'Technical',
        status: 'Active',
        description: 'Information Technology department'
      },
      {
        name: 'Finance Team',
        code: 'FIN-TEAM',
        type: 'Business Support',
        status: 'Active',
        description: 'Financial operations and accounting'
      },
      {
        name: 'London Office',
        code: 'LON-OFF',
        type: 'Geography',
        status: 'Active',
        description: 'London headquarters office'
      }
    ];

    try {
      let created = 0;
      for (const unit of testUnits) {
        try {
          await apiCall('POST', '/boost/business-units', unit);
          created++;
        } catch (error) {
          // Unit might already exist, skip
        }
      }
      
      toast({
        title: "Success",
        description: `Created ${created} test business units`,
      });
      
      fetchBusinessUnits();
    } catch (error) {
      console.error('Error creating test business units:', error);
      toast({
        title: "Error",
        description: "Failed to create test business units",
        variant: "destructive"
      });
    }
  };

  const fetchUsers = async () => {
    try {
      const data = await apiCall('GET', '/boost/users');
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchBusinessUnits = async () => {
    try {
      const data = await apiCall('GET', '/boost/business-units');
      setBusinessUnits(data);
    } catch (error) {
      console.error('Error fetching business units:', error);
    }
  };

  const updateUserRole = async (userId, newRole) => {
    try {
      await apiCall('PUT', `/boost/users/${userId}`, { boost_role: newRole });
      toast({
        title: "Success",
        description: "User role updated successfully",
      });
      fetchUsers();
    } catch (error) {
      console.error('Error updating user role:', error);
    }
  };

  const deleteUser = async (userId) => {
    try {
      await apiCall('DELETE', `/boost/users/${userId}`);
      toast({
        title: "Success",
        description: "User deleted successfully",
      });
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  };

  const deleteBusinessUnit = async (unitId) => {
    try {
      await apiCall('DELETE', `/boost/business-units/${unitId}`);
      toast({
        title: "Success",
        description: "Business unit deleted successfully",
      });
      fetchBusinessUnits();
    } catch (error) {
      console.error('Error deleting business unit:', error);
    }
  };

  const getRoleColor = (role) => {
    const colors = {
      Admin: 'bg-red-100 text-red-700',
      Manager: 'bg-orange-100 text-orange-700',
      Agent: 'bg-blue-100 text-blue-700',
      User: 'bg-gray-100 text-gray-700'
    };
    return colors[role] || colors.User;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">BOOST Admin</h1>
          <p className="text-gray-600 mt-2">Manage users and business units</p>
        </div>
        <div className="flex flex-col space-y-2">
          <Button 
            onClick={createTestUsers}
            variant="outline"
            size="sm"
            className="border-blue-200 text-blue-600 hover:bg-blue-50"
          >
            <Users className="w-4 h-4 mr-2" />
            Create Test Users
          </Button>
          <Button 
            onClick={createTestBusinessUnits}
            variant="outline"
            size="sm"
            className="border-purple-200 text-purple-600 hover:bg-purple-50"
          >
            <Building2 className="w-4 h-4 mr-2" />
            Create Test Units
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="units">Business Units</TabsTrigger>
          <TabsTrigger value="testing">Test Data</TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Users Management</CardTitle>
                <Button onClick={() => setShowNewUserModal(true)} className="bg-emerald-600 hover:bg-emerald-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Add User
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3">Name</th>
                      <th className="text-left p-3">Email</th>
                      <th className="text-left p-3">BOOST Role</th>
                      <th className="text-left p-3">Business Unit</th>
                      <th className="text-left p-3">BOOST Department</th>
                      <th className="text-left p-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(user => (
                      <tr key={user.id} className="border-b hover:bg-gray-50">
                        <td className="p-3 font-medium">{user.name}</td>
                        <td className="p-3 text-gray-600">{user.email}</td>
                        <td className="p-3">
                          <Select 
                            value={user.boost_role} 
                            onValueChange={(newRole) => updateUserRole(user.id, newRole)}
                          >
                            <SelectTrigger className="w-32">
                              <Badge className={getRoleColor(user.boost_role)}>
                                {user.boost_role}
                              </Badge>
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Admin">Admin</SelectItem>
                              <SelectItem value="Manager">Manager</SelectItem>
                              <SelectItem value="Agent">Agent</SelectItem>
                              <SelectItem value="User">User</SelectItem>
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="p-3 text-gray-600">{user.business_unit_name || 'None'}</td>
                        <td className="p-3 text-gray-600">{user.department || 'None'}</td>
                        <td className="p-3">
                          <div className="flex space-x-1">
                            <Button size="sm" variant="outline" onClick={() => setEditingUser(user)}>
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => deleteUser(user.id)}>
                              <Trash2 className="w-3 h-3 text-red-600" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="units" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Business Units Management</CardTitle>
                <Button onClick={() => setShowNewUnitModal(true)} className="bg-emerald-600 hover:bg-emerald-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Unit
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {businessUnits.map(unit => (
                  <Card key={unit.id} className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">{unit.name}</h3>
                      <div className="flex space-x-1">
                        <Button size="sm" variant="outline" onClick={() => setEditingUnit(unit)}>
                          <Edit className="w-3 h-3" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => deleteBusinessUnit(unit.id)}>
                          <Trash2 className="w-3 h-3 text-red-600" />
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600">Code: {unit.code || 'None'}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      Created {new Date(unit.created_at).toLocaleDateString()}
                    </p>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="testing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Test Data Management</CardTitle>
              <CardDescription>Create dummy accounts and business units for testing BOOST functionality</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Test Users Section */}
              <div>
                <h3 className="text-lg font-medium mb-3">Test User Accounts</h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-blue-800 mb-3">
                    Creates 8 test accounts with different roles and departments for comprehensive testing:
                  </p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <strong className="text-blue-900">Admin & Management:</strong>
                      <ul className="ml-4 mt-1 space-y-1">
                        <li>• admin@company.test (Admin)</li>
                        <li>• manager@company.test (Manager)</li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-blue-900">Department Agents:</strong>
                      <ul className="ml-4 mt-1 space-y-1">
                        <li>• finance.agent@company.test</li>
                        <li>• hr.agent@company.test</li>
                        <li>• it.agent@company.test</li>
                        <li>• devops.agent@company.test</li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-blue-900">End Users:</strong>
                      <ul className="ml-4 mt-1 space-y-1">
                        <li>• user.one@company.test</li>
                        <li>• user.two@company.test</li>
                      </ul>
                    </div>
                  </div>
                </div>
                <Button 
                  onClick={createTestUsers}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Users className="w-4 h-4 mr-2" />
                  Create Test User Accounts
                </Button>
              </div>

              {/* Test Business Units Section */}
              <div>
                <h3 className="text-lg font-medium mb-3">Test Business Units</h3>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-purple-800 mb-3">
                    Creates 5 business units across different types for testing organizational structure:
                  </p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <strong className="text-purple-900">Geography:</strong>
                      <ul className="ml-4 mt-1 space-y-1">
                        <li>🌍 Africa Division (AFR001)</li>
                        <li>🌏 Asia Pacific (APAC001)</li>
                        <li>🏢 London Office (LON-OFF)</li>
                      </ul>
                    </div>
                    <div>
                      <strong className="text-purple-900">Departments:</strong>
                      <ul className="ml-4 mt-1 space-y-1">
                        <li>⚙️ IT Department (IT-DEPT)</li>
                        <li>💼 Finance Team (FIN-TEAM)</li>
                      </ul>
                    </div>
                  </div>
                </div>
                <Button 
                  onClick={createTestBusinessUnits}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Building2 className="w-4 h-4 mr-2" />
                  Create Test Business Units
                </Button>
              </div>

              {/* Testing Instructions */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Testing Instructions</h4>
                <div className="text-sm text-gray-700 space-y-2">
                  <p><strong>1. Role-based Testing:</strong> Use different user accounts to test role-based permissions and ticket visibility.</p>
                  <p><strong>2. Department Testing:</strong> Assign agents to different departments to test department-specific ticket access.</p>
                  <p><strong>3. Assignment Testing:</strong> Use Manager/Admin accounts to test ticket assignment to various agents.</p>
                  <p><strong>4. Business Unit Testing:</strong> Create tickets with different business units to test organizational routing.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* New User Modal */}
      <BoostUserModal
        isOpen={showNewUserModal}
        onClose={() => setShowNewUserModal(false)}
        user={null}
        businessUnits={businessUnits}
        onSave={() => {
          setShowNewUserModal(false);
          fetchUsers();
        }}
      />

      {/* Edit User Modal */}
      <BoostUserModal
        isOpen={!!editingUser}
        onClose={() => setEditingUser(null)}
        user={editingUser}
        businessUnits={businessUnits}
        onSave={() => {
          setEditingUser(null);
          fetchUsers();
        }}
      />

      {/* New Unit Modal */}
      <BoostUnitModal
        isOpen={showNewUnitModal}
        onClose={() => setShowNewUnitModal(false)}
        unit={null}
        onSave={() => {
          setShowNewUnitModal(false);
          fetchBusinessUnits();
        }}
      />

      {/* Edit Unit Modal */}
      <BoostUnitModal
        isOpen={!!editingUnit}
        onClose={() => setEditingUnit(null)}
        unit={editingUnit}
        onSave={() => {
          setEditingUnit(null);
          fetchBusinessUnits();
        }}
      />
    </div>
  );
};

// BOOST User Modal Component
const BoostUserModal = ({ isOpen, onClose, user, businessUnits, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    boost_role: 'User',
    business_unit_id: '',
    department: ''
  });
  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name,
        email: user.email,
        boost_role: user.boost_role,
        business_unit_id: user.business_unit_id || '',
        department: user.department || ''
      });
    } else {
      setFormData({
        name: '',
        email: '',
        boost_role: 'User',
        business_unit_id: '',
        department: ''
      });
    }
  }, [user]);

  const handleSubmit = async () => {
    try {
      if (user) {
        await apiCall('PUT', `/boost/users/${user.id}`, formData);
        toast({ title: "Success", description: "User updated successfully" });
      } else {
        await apiCall('POST', '/boost/users', formData);
        toast({ title: "Success", description: "User created successfully" });
      }
      onSave();
    } catch (error) {
      console.error('Error saving user:', error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{user ? 'Edit User' : 'Add New User'}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Name</Label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="Full name"
            />
          </div>
          <div>
            <Label>Email</Label>
            <Input
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              placeholder="email@company.com"
              type="email"
            />
          </div>
          <div>
            <Label>BOOST Role</Label>
            <Select value={formData.boost_role} onValueChange={(value) => setFormData({...formData, boost_role: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Admin">Admin</SelectItem>
                <SelectItem value="Manager">Manager</SelectItem>
                <SelectItem value="Agent">Agent</SelectItem>
                <SelectItem value="User">User</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Business Unit</Label>
            <Select value={formData.business_unit_id} onValueChange={(value) => setFormData({...formData, business_unit_id: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Select business unit" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {businessUnits.map(unit => (
                  <SelectItem key={unit.id} value={unit.id}>{unit.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Department</Label>
            <Select value={formData.department} onValueChange={(value) => setFormData({...formData, department: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Select department" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="OS Support">OS Support</SelectItem>
                <SelectItem value="Finance">Finance</SelectItem>
                <SelectItem value="HR/P&T">HR/P&T</SelectItem>
                <SelectItem value="IT">IT</SelectItem>
                <SelectItem value="DevOps">DevOps</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSubmit} className="bg-emerald-600 hover:bg-emerald-700">
              {user ? 'Update' : 'Create'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// BOOST Unit Modal Component
const BoostUnitModal = ({ isOpen, onClose, unit, onSave }) => {
  const [formData, setFormData] = useState({ 
    name: '', 
    code: '', 
    type: 'Business Support',
    status: 'Active',
    description: ''
  });
  const { apiCall } = useAPI();
  const { toast } = useToast();

  const businessUnitTypes = [
    'Geography',
    'Business Support', 
    'Technical',
    'Other'
  ];

  useEffect(() => {
    if (unit) {
      setFormData({ 
        name: unit.name, 
        code: unit.code || '',
        type: unit.type || 'Business Support',
        status: unit.status || 'Active',
        description: unit.description || ''
      });
    } else {
      setFormData({ 
        name: '', 
        code: '', 
        type: 'Business Support',
        status: 'Active',
        description: ''
      });
    }
  }, [unit]);

  const handleSubmit = async () => {
    try {
      if (unit) {
        await apiCall('PUT', `/boost/business-units/${unit.id}`, formData);
        toast({ title: "Success", description: "Business unit updated successfully" });
      } else {
        await apiCall('POST', '/boost/business-units', formData);
        toast({ title: "Success", description: "Business unit created successfully" });
      }
      onSave();
    } catch (error) {
      console.error('Error saving business unit:', error);
      toast({ 
        title: "Error", 
        description: "Failed to save business unit",
        variant: "destructive"
      });
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'Geography': return '🌍';
      case 'Technical': return '⚙️';
      case 'Business Support': return '💼';
      case 'Other': return '📁';
      default: return '📁';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{unit ? 'Edit Business Unit' : 'Add New Business Unit'}</DialogTitle>
          <DialogDescription>
            {unit ? 'Update business unit information' : 'Create a new business unit to organize requesters and route tickets'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Name *</Label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="e.g., Africa Division, IT Department, London Office"
            />
          </div>
          
          <div>
            <Label>Code</Label>
            <Input
              value={formData.code}
              onChange={(e) => setFormData({...formData, code: e.target.value})}
              placeholder="e.g., AFR001, IT-LON, BIZ-SUP"
            />
          </div>

          <div>
            <Label>Type *</Label>
            <Select value={formData.type} onValueChange={(value) => setFormData({...formData, type: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {businessUnitTypes.map(type => (
                  <SelectItem key={type} value={type}>
                    <span className="flex items-center">
                      <span className="mr-2">{getTypeIcon(type)}</span>
                      {type}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500 mt-1">
              Geography: Regional offices • Technical: IT/Engineering • Business Support: HR/Finance • Other: Miscellaneous
            </p>
          </div>

          <div>
            <Label>Status</Label>
            <Select value={formData.status} onValueChange={(value) => setFormData({...formData, status: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Active">✅ Active</SelectItem>
                <SelectItem value="Inactive">⏸️ Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Description</Label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Brief description of this business unit's purpose..."
              rows={3}
            />
          </div>
          
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button 
              onClick={handleSubmit} 
              className="bg-emerald-600 hover:bg-emerald-700"
              disabled={!formData.name.trim()}
            >
              {unit ? 'Update Unit' : 'Create Unit'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// System Admin Dashboard Component
const SystemAdmin = () => {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [businessUnits, setBusinessUnits] = useState([]);
  const [permissions, setPermissions] = useState({});
  const [systemStats, setSystemStats] = useState({});
  const [selectedUser, setSelectedUser] = useState(null);
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [showBusinessUnitModal, setShowBusinessUnitModal] = useState(false);
  const [editingUnit, setEditingUnit] = useState(null);
  const [showUserEditModal, setShowUserEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  
  const { apiCall } = useAPI();
  const { toast } = useToast();

  // Permission categories and their specific permissions
  const permissionCategories = {
    'Dashboard': [
      'view_dashboard',
      'view_statistics',
      'export_reports'
    ],
    'Ashur': [
      'use_ai_chat',
      'view_chat_history',
      'delete_conversations'
    ],
    'BOOST Support': [
      'create_tickets',
      'view_own_tickets',
      'view_department_tickets',
      'view_all_tickets',
      'assign_tickets',
      'close_tickets',
      'delete_tickets'
    ],
    'Knowledge Base': [
      'view_documents',
      'upload_documents',
      'approve_documents',
      'manage_documents',
      'admin_documents'
    ],
    'Administration': [
      'manage_users',
      'manage_business_units',
      'manage_permissions',
      'system_settings',
      'view_audit_logs'
    ]
  };

  useEffect(() => {
    fetchUsers();
    fetchBusinessUnits();
    fetchSystemStats();
    fetchPermissions();
  }, []);

  const fetchUsers = async () => {
    try {
      const boostUsers = await apiCall('GET', '/boost/users');
      setUsers(boostUsers);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchBusinessUnits = async () => {
    try {
      const units = await apiCall('GET', '/boost/business-units');
      setBusinessUnits(units);
    } catch (error) {
      console.error('Error fetching business units:', error);
    }
  };

  const fetchSystemStats = async () => {
    try {
      // Get various statistics from different endpoints
      const [tickets, documents, ragStats] = await Promise.all([
        apiCall('GET', '/boost/tickets'),
        apiCall('GET', '/documents?show_all=true'),
        apiCall('GET', '/documents/rag-stats')
      ]);

      setSystemStats({
        totalTickets: tickets.length,
        openTickets: tickets.filter(t => t.status === 'open').length,
        totalDocuments: documents.length,
        approvedDocuments: documents.filter(d => d.approval_status === 'approved').length,
        totalUsers: users.length,
        totalBusinessUnits: businessUnits.length,
        ragStats: ragStats
      });
    } catch (error) {
      console.error('Error fetching system stats:', error);
    }
  };

  const fetchPermissions = async () => {
    // For now, create default permissions structure
    const defaultPermissions = {};
    users.forEach(user => {
      defaultPermissions[user.id] = getDefaultPermissions(user.boost_role);
    });
    setPermissions(defaultPermissions);
  };

  const getDefaultPermissions = (role) => {
    const allPermissions = Object.values(permissionCategories).flat();
    
    switch (role) {
      case 'Admin':
        return Object.fromEntries(allPermissions.map(p => [p, true]));
      case 'Manager':
        return {
          view_dashboard: true,
          view_statistics: true,
          export_reports: true,
          use_ai_chat: true,
          view_chat_history: true,
          delete_conversations: true,
          create_tickets: true,
          view_own_tickets: true,
          view_department_tickets: true,
          view_all_tickets: true,
          assign_tickets: true,
          close_tickets: true,
          view_documents: true,
          upload_documents: true,
          approve_documents: true,
          manage_documents: true,
          manage_users: false,
          manage_business_units: false,
          manage_permissions: false,
          system_settings: false,
          view_audit_logs: true
        };
      case 'Agent':
        return {
          view_dashboard: true,
          view_statistics: false,
          export_reports: false,
          use_ai_chat: true,
          view_chat_history: true,
          delete_conversations: false,
          create_tickets: true,
          view_own_tickets: true,
          view_department_tickets: true,
          view_all_tickets: false,
          assign_tickets: false,
          close_tickets: false,
          delete_tickets: false,
          view_documents: true,
          upload_documents: true,
          approve_documents: false,
          manage_documents: false,
          admin_documents: false
        };
      case 'User':
        return {
          view_dashboard: true,
          view_statistics: false,
          use_ai_chat: true,
          view_chat_history: true,
          create_tickets: true,
          view_own_tickets: true,
          view_documents: true,
          upload_documents: true
        };
      default:
        return Object.fromEntries(allPermissions.map(p => [p, false]));
    }
  };

  const updateUserPermissions = async (userId, newPermissions) => {
    try {
      // TODO: Save to backend when permissions API is available
      // await apiCall('PUT', `/boost/users/${userId}/permissions`, newPermissions);
      
      setPermissions(prev => ({
        ...prev,
        [userId]: newPermissions
      }));
      
      toast({
        title: "Success",
        description: "User permissions updated successfully",
      });
    } catch (error) {
      console.error('Error updating permissions:', error);
      toast({
        title: "Error",
        description: "Failed to update permissions",
        variant: "destructive"
      });
    }
  };

  const createBusinessUnit = async (unitData) => {
    try {
      await apiCall('POST', '/boost/business-units', unitData);
      toast({
        title: "Success",
        description: "Business unit created successfully",
      });
      fetchBusinessUnits();
      setShowBusinessUnitModal(false);
    } catch (error) {
      console.error('Error creating business unit:', error);
      toast({
        title: "Error",
        description: "Failed to create business unit",
        variant: "destructive"
      });
    }
  };

  const updateBusinessUnit = async (unitId, unitData) => {
    try {
      await apiCall('PUT', `/boost/business-units/${unitId}`, unitData);
      toast({
        title: "Success", 
        description: "Business unit updated successfully",
      });
      fetchBusinessUnits();
      setShowBusinessUnitModal(false);
      setEditingUnit(null);
    } catch (error) {
      console.error('Error updating business unit:', error);
      toast({
        title: "Error",
        description: "Failed to update business unit",
        variant: "destructive"
      });
    }
  };

  const deleteBusinessUnit = async (unitId) => {
    if (!confirm('Are you sure you want to delete this business unit?')) return;
    
    try {
      await apiCall('DELETE', `/boost/business-units/${unitId}`);
      toast({
        title: "Success",
        description: "Business unit deleted successfully",
      });
      fetchBusinessUnits();
    } catch (error) {
      console.error('Error deleting business unit:', error);
      toast({
        title: "Error",
        description: "Failed to delete business unit",
        variant: "destructive"
      });
    }
  };

  const editUser = (user) => {
    setEditingUser(user);
    setShowUserEditModal(true);
  };

  const manageUserPermissions = (user) => {
    setSelectedUser(user);
    setShowPermissionModal(true);
  };

  const deleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
    
    try {
      await apiCall('DELETE', `/boost/users/${userId}`);
      toast({
        title: "Success",
        description: "User deleted successfully",
      });
      fetchUsers();
      // Remove user from permissions state
      setPermissions(prev => {
        const newPerms = { ...prev };
        delete newPerms[userId];
        return newPerms;
      });
    } catch (error) {
      console.error('Error deleting user:', error);
      toast({
        title: "Error",
        description: "Failed to delete user",
        variant: "destructive"
      });
    }
  };

  const updateUser = async (userId, userData) => {
    try {
      await apiCall('PUT', `/boost/users/${userId}`, userData);
      toast({
        title: "Success",
        description: "User updated successfully",
      });
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      toast({
        title: "Error",
        description: "Failed to update user",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Administration</h1>
          <p className="text-gray-600 mt-2">Manage users, permissions, and system configuration</p>
        </div>
        <Button 
          onClick={fetchSystemStats}
          variant="outline"
          className="border-emerald-200 text-emerald-600 hover:bg-emerald-50"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh Stats
        </Button>
      </div>

      {/* System Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Ticket className="w-8 h-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Tickets</p>
                <p className="text-2xl font-bold text-gray-900">{systemStats.totalTickets || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <AlertCircle className="w-8 h-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Open Tickets</p>
                <p className="text-2xl font-bold text-gray-900">{systemStats.openTickets || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <FileText className="w-8 h-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Documents</p>
                <p className="text-2xl font-bold text-gray-900">{systemStats.totalDocuments || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Users className="w-8 h-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Users</p>
                <p className="text-2xl font-bold text-gray-900">{users.length || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="users">Users & Permissions</TabsTrigger>
          <TabsTrigger value="business">Business Units</TabsTrigger>
          <TabsTrigger value="system">System Settings</TabsTrigger>
          <TabsTrigger value="audit">Audit Logs</TabsTrigger>
        </TabsList>

        {/* Users & Permissions Tab */}
        <TabsContent value="users" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>User Management & Permissions</CardTitle>
                <Button 
                  onClick={() => {
                    setSelectedUser(null);
                    setShowPermissionModal(true);
                  }}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add User
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3">User</th>
                      <th className="text-left p-3">Role</th>
                      <th className="text-left p-3">Department</th>
                      <th className="text-left p-3">Business Unit</th>
                      <th className="text-left p-3">Permissions</th>
                      <th className="text-left p-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(user => (
                      <tr key={user.id} className="border-b hover:bg-gray-50">
                        <td className="p-3">
                          <div>
                            <div className="font-medium">{user.name}</div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                          </div>
                        </td>
                        <td className="p-3">
                          <Badge className={`${
                            user.boost_role === 'Admin' ? 'bg-red-100 text-red-700' :
                            user.boost_role === 'Manager' ? 'bg-orange-100 text-orange-700' :
                            user.boost_role === 'Agent' ? 'bg-blue-100 text-blue-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {user.boost_role}
                          </Badge>
                        </td>
                        <td className="p-3 text-gray-600">{user.department || 'None'}</td>
                        <td className="p-3 text-gray-600">{user.business_unit_name || 'None'}</td>
                        <td className="p-3">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => manageUserPermissions(user)}
                            title="Manage user permissions"
                          >
                            <Settings className="w-3 h-3 mr-1" />
                            Manage
                          </Button>
                        </td>
                        <td className="p-3">
                          <div className="flex space-x-1">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => editUser(user)}
                              title="Edit user details and permissions"
                            >
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="text-red-600 hover:bg-red-50"
                              onClick={() => deleteUser(user.id)}
                              title="Delete user permanently"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Business Units Tab */}
        <TabsContent value="business" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Business Units Management</CardTitle>
                <Button 
                  onClick={() => {
                    setEditingUnit(null);
                    setShowBusinessUnitModal(true);
                  }}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Business Unit
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {businessUnits.map(unit => (
                  <Card key={unit.id} className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">
                          {unit.type === 'Geography' ? '🌍' :
                           unit.type === 'Technical' ? '⚙️' :
                           unit.type === 'Business Support' ? '💼' : '📁'}
                        </span>
                        <div>
                          <h3 className="font-medium">{unit.name}</h3>
                          <p className="text-sm text-gray-500">{unit.type}</p>
                        </div>
                      </div>
                      <div className="flex space-x-1">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            setEditingUnit(unit);
                            setShowBusinessUnitModal(true);
                          }}
                        >
                          <Edit className="w-3 h-3" />
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => deleteBusinessUnit(unit.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                    <div className="space-y-1 text-sm">
                      <p><strong>Code:</strong> {unit.code || 'None'}</p>
                      <p><strong>Status:</strong> 
                        <Badge variant="outline" className="ml-1">
                          {unit.status || 'Active'}
                        </Badge>
                      </p>
                      <p className="text-gray-500 mt-2">{unit.description}</p>
                    </div>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Settings Tab */}
        <TabsContent value="system" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-3">General Settings</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span>Allow user registration</span>
                      <input type="checkbox" className="toggle" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Require document approval</span>
                      <input type="checkbox" className="toggle" defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Enable audit logging</span>
                      <input type="checkbox" className="toggle" defaultChecked />
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-3">AI Settings</h3>
                  <div className="space-y-3">
                    <div>
                      <Label>Default AI Model</Label>
                      <Select defaultValue="gpt-5">
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="gpt-5">GPT-5</SelectItem>
                          <SelectItem value="claude-4">Claude Sonnet 4</SelectItem>
                          <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Audit Logs Tab */}
        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System Audit Logs</CardTitle>
              <CardDescription>Track all system activities and changes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-gray-500">
                <Clock className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p>Audit logging system will be implemented here</p>
                <p className="text-sm">Track user actions, permission changes, and system events</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Permission Management Modal */}
      <PermissionModal
        isOpen={showPermissionModal}
        onClose={() => {
          setShowPermissionModal(false);
          setSelectedUser(null);
        }}
        user={selectedUser}
        permissionCategories={permissionCategories}
        permissions={permissions[selectedUser?.id] || {}}
        businessUnits={businessUnits}
        onSave={(data) => {
          if (selectedUser) {
            if (data.isUpdate) {
              // Updating existing user details and permissions
              updateUserPermissions(selectedUser.id, data.permissions);
              fetchUsers(); // Refresh user list to show updated details
            } else {
              // Only updating permissions
              updateUserPermissions(selectedUser.id, data);
            }
          } else {
            // Creating new user with permissions
            updateUserPermissions(data.user.id, data.permissions);
            fetchUsers(); // Refresh user list
          }
          setShowPermissionModal(false);
          setSelectedUser(null);
        }}
      />

      {/* User Edit Modal */}
      <UserEditModal
        isOpen={showUserEditModal}
        onClose={() => {
          setShowUserEditModal(false);
          setEditingUser(null);
        }}
        user={editingUser}
        businessUnits={businessUnits}
        onSave={async (userData) => {
          try {
            if (editingUser) {
              await updateUser(editingUser.id, userData);
            } else {
              // This modal is only for editing, not creating
              console.log('UserEditModal should only be used for editing');
            }
            setShowUserEditModal(false);
            setEditingUser(null);
          } catch (error) {
            console.error('Error in UserEditModal save:', error);
          }
        }}
      />

      {/* Business Unit Modal */}
      <BusinessUnitManagementModal
        isOpen={showBusinessUnitModal}
        onClose={() => {
          setShowBusinessUnitModal(false);
          setEditingUnit(null);
        }}
        unit={editingUnit}
        onSave={(unitData) => {
          if (editingUnit) {
            updateBusinessUnit(editingUnit.id, unitData);
          } else {
            createBusinessUnit(unitData);
          }
        }}
      />
    </div>
  );
};

// Enhanced Permission Management Modal Component with User Creation
const PermissionModal = ({ isOpen, onClose, user, permissionCategories, permissions, onSave, businessUnits = [] }) => {
  const [localPermissions, setLocalPermissions] = useState(permissions);
  const [userForm, setUserForm] = useState({
    name: '',
    email: '',
    boost_role: 'User',
    department: '',
    business_unit_id: ''
  });
  const { apiCall } = useAPI();
  const { toast } = useToast();

  useEffect(() => {
    setLocalPermissions(permissions);
    if (user) {
      setUserForm({
        name: user.name,
        email: user.email,
        boost_role: user.boost_role,
        department: user.department || '',
        business_unit_id: user.business_unit_id || ''
      });
    } else {
      setUserForm({
        name: '',
        email: '',
        boost_role: 'User',
        department: '',
        business_unit_id: ''
      });
    }
  }, [permissions, user]);

  const handlePermissionChange = (permission, value) => {
    setLocalPermissions(prev => ({
      ...prev,
      [permission]: value
    }));
  };

  const handleRoleChange = (newRole) => {
    setUserForm(prev => ({ ...prev, boost_role: newRole }));
    // Auto-set permissions based on role
    const defaultPermissions = getDefaultPermissions(newRole);
    setLocalPermissions(defaultPermissions);
  };

  const getDefaultPermissions = (role) => {
    const allPermissions = Object.values(permissionCategories).flat();
    
    switch (role) {
      case 'Admin':
        return Object.fromEntries(allPermissions.map(p => [p, true]));
      case 'Manager':
        return {
          view_dashboard: true,
          view_statistics: true,
          export_reports: true,
          use_ai_chat: true,
          view_chat_history: true,
          delete_conversations: true,
          create_tickets: true,
          view_own_tickets: true,
          view_department_tickets: true,
          view_all_tickets: true,
          assign_tickets: true,
          close_tickets: true,
          view_documents: true,
          upload_documents: true,
          approve_documents: true,
          manage_documents: true,
          manage_users: false,
          manage_business_units: false,
          manage_permissions: false,
          system_settings: false,
          view_audit_logs: true
        };
      case 'Agent':
        return {
          view_dashboard: true,
          view_statistics: false,
          export_reports: false,
          use_ai_chat: true,
          view_chat_history: true,
          delete_conversations: false,
          create_tickets: true,
          view_own_tickets: true,
          view_department_tickets: true,
          view_all_tickets: false,
          assign_tickets: false,
          close_tickets: false,
          delete_tickets: false,
          view_documents: true,
          upload_documents: true,
          approve_documents: false,
          manage_documents: false,
          admin_documents: false
        };
      case 'User':
        return {
          view_dashboard: true,
          view_statistics: false,
          use_ai_chat: true,
          view_chat_history: true,
          create_tickets: true,
          view_own_tickets: true,
          view_documents: true,
          upload_documents: true
        };
      default:
        return Object.fromEntries(allPermissions.map(p => [p, false]));
    }
  };

  const handleSave = async () => {
    try {
      if (!user) {
        // Creating new user
        if (!userForm.name.trim() || !userForm.email.trim()) {
          toast({
            title: "Validation Error",
            description: "Name and email are required",
            variant: "destructive"
          });
          return;
        }

        // Create user first
        const newUser = await apiCall('POST', '/boost/users', userForm);
        
        toast({
          title: "Success",
          description: "User created successfully with permissions",
        });
        
        // Pass both user data and permissions
        onSave({ user: newUser, permissions: localPermissions });
      } else {
        // Updating existing user - update both user details and permissions
        if (!userForm.name.trim() || !userForm.email.trim()) {
          toast({
            title: "Validation Error",
            description: "Name and email are required",
            variant: "destructive"
          });
          return;
        }

        // Update user details first
        await apiCall('PUT', `/boost/users/${user.id}`, userForm);
        
        toast({
          title: "Success",
          description: "User updated successfully with permissions",
        });

        // Pass both user data and permissions for existing user updates
        onSave({ user: userForm, permissions: localPermissions, isUpdate: true });
      }
    } catch (error) {
      console.error('Error saving user/permissions:', error);
      toast({
        title: "Error",
        description: "Failed to save user/permissions",
        variant: "destructive"
      });
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {user ? `Manage Permissions - ${user.name}` : 'Create New User'}
          </DialogTitle>
          <DialogDescription>
            {user ? 
              `Configure specific permissions for ${user.name} (${user.boost_role})` :
              'Set up a new user account with appropriate permissions'
            }
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* User Details Form (for new users) */}
          {!user && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">User Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Name *</Label>
                    <Input
                      value={userForm.name}
                      onChange={(e) => setUserForm({...userForm, name: e.target.value})}
                      placeholder="Full name"
                    />
                  </div>
                  <div>
                    <Label>Email *</Label>
                    <Input
                      type="email"
                      value={userForm.email}
                      onChange={(e) => setUserForm({...userForm, email: e.target.value})}
                      placeholder="user@company.com"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Role</Label>
                    <Select value={userForm.boost_role} onValueChange={handleRoleChange}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="User">User</SelectItem>
                        <SelectItem value="Agent">Agent</SelectItem>
                        <SelectItem value="Manager">Manager</SelectItem>
                        <SelectItem value="Admin">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>BOOST Department</Label>
                    <Select value={userForm.department || ""} onValueChange={(value) => setUserForm({...userForm, department: value === "none" ? null : value})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select BOOST department" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="OS Support">OS Support</SelectItem>
                        <SelectItem value="Finance">Finance</SelectItem>
                        <SelectItem value="HR/P&T">HR/P&T</SelectItem>
                        <SelectItem value="IT">IT</SelectItem>
                        <SelectItem value="DevOps">DevOps</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Business Unit</Label>
                  <Select value={userForm.business_unit_id} onValueChange={(value) => setUserForm({...userForm, business_unit_id: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select business unit" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      {businessUnits.map(unit => (
                        <SelectItem key={unit.id} value={unit.id}>{unit.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Permissions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Permissions Configuration</CardTitle>
              {!user && (
                <CardDescription>
                  Permissions are automatically set based on role, but can be customized below
                </CardDescription>
              )}
            </CardHeader>
            <CardContent>
              {/* Select All Controls */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
                <div className="flex items-center justify-between">
                  <h3 className="text-md font-medium text-gray-900">Quick Actions</h3>
                  <div className="flex space-x-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const allPermissions = Object.values(permissionCategories).flat();
                        const allSelected = Object.fromEntries(allPermissions.map(p => [p, true]));
                        setLocalPermissions(allSelected);
                      }}
                      className="bg-emerald-600 text-white hover:bg-emerald-700"
                    >
                      Select All
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const allPermissions = Object.values(permissionCategories).flat();
                        const noneSelected = Object.fromEntries(allPermissions.map(p => [p, false]));
                        setLocalPermissions(noneSelected);
                      }}
                    >
                      Deselect All
                    </Button>
                  </div>
                </div>
              </div>

              {Object.entries(permissionCategories).map(([category, categoryPermissions]) => (
                <div key={category} className="mb-6">
                  <h3 className="text-md font-medium mb-3 flex items-center border-b pb-2">
                    {category === 'Dashboard' && <BarChart3 className="w-4 h-4 mr-2" />}
                    {category === 'Ashur' && <MessageCircle className="w-4 h-4 mr-2" />}
                    {category === 'BOOST Support' && <Ticket className="w-4 h-4 mr-2" />}
                    {category === 'Knowledge Base' && <FileText className="w-4 h-4 mr-2" />}
                    {category === 'Administration' && <Shield className="w-4 h-4 mr-2" />}
                    {category}
                  </h3>
                  <div className="grid grid-cols-1 gap-2 pl-6">
                    {categoryPermissions.map(permission => (
                      <div key={permission} className="flex items-center justify-between py-1">
                        <span className="text-sm text-gray-700">
                          {permission.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                        <input
                          type="checkbox"
                          checked={localPermissions[permission] || false}
                          onChange={(e) => handlePermissionChange(permission, e.target.checked)}
                          className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end space-x-2 pt-4">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} className="bg-emerald-600 hover:bg-emerald-700">
            {user ? 'Save Permissions' : 'Create User'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// User Edit Modal Component (separate from permissions)
const UserEditModal = ({ isOpen, onClose, user, businessUnits = [], onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    boost_role: 'User',
    department: '',
    business_unit_id: ''
  });
  const { toast } = useToast();

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || '',
        email: user.email || '',
        boost_role: user.boost_role || 'User',
        department: user.department || '',
        business_unit_id: user.business_unit_id || ''
      });
    } else {
      setFormData({
        name: '',
        email: '',
        boost_role: 'User',
        department: '',
        business_unit_id: ''
      });
    }
  }, [user]);

  const handleSubmit = async () => {
    if (!formData.name.trim() || !formData.email.trim()) {
      toast({
        title: "Validation Error",
        description: "Name and email are required",
        variant: "destructive"
      });
      return;
    }

    onSave(formData);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {user ? `Edit User - ${user.name}` : 'Create New User'}
          </DialogTitle>
          <DialogDescription>
            Update user credentials and basic information
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Full name"
              />
            </div>
            <div>
              <Label>Email *</Label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="user@company.com"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Role</Label>
              <Select value={formData.boost_role} onValueChange={(value) => setFormData({...formData, boost_role: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="User">User</SelectItem>
                  <SelectItem value="Agent">Agent</SelectItem>
                  <SelectItem value="Manager">Manager</SelectItem>
                  <SelectItem value="Admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>BOOST Department</Label>
              <Select value={formData.department || ""} onValueChange={(value) => setFormData({...formData, department: value === "none" ? null : value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select BOOST department" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="OS Support">OS Support</SelectItem>
                  <SelectItem value="Finance">Finance</SelectItem>
                  <SelectItem value="HR/P&T">HR/P&T</SelectItem>
                  <SelectItem value="IT">IT</SelectItem>
                  <SelectItem value="DevOps">DevOps</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label>Business Unit</Label>
            <Select value={formData.business_unit_id} onValueChange={(value) => setFormData({...formData, business_unit_id: value})}>
              <SelectTrigger>
                <SelectValue placeholder="Select business unit" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">None</SelectItem>
                {businessUnits.map(unit => (
                  <SelectItem key={unit.id} value={unit.id}>{unit.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex justify-end space-x-2 pt-4">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            onClick={handleSubmit}
            className="bg-emerald-600 hover:bg-emerald-700"
            disabled={!formData.name.trim() || !formData.email.trim()}
          >
            {user ? 'Update User' : 'Create User'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Business Unit Management Modal Component  
const BusinessUnitManagementModal = ({ isOpen, onClose, unit, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    type: 'Business Support',
    status: 'Active',
    description: ''
  });

  const businessUnitTypes = [
    'Geography',
    'Business Support',
    'Technical', 
    'Other'
  ];

  useEffect(() => {
    if (unit) {
      setFormData({
        name: unit.name || '',
        code: unit.code || '',
        type: unit.type || 'Business Support',
        status: unit.status || 'Active',
        description: unit.description || ''
      });
    } else {
      setFormData({
        name: '',
        code: '',
        type: 'Business Support',
        status: 'Active',
        description: ''
      });
    }
  }, [unit]);

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      alert('Business unit name is required');
      return;
    }
    onSave(formData);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {unit ? 'Edit Business Unit' : 'Create Business Unit'}  
          </DialogTitle>
          <DialogDescription>
            {unit ? 
              'Update business unit information and organizational structure' :
              'Create a new business unit to organize users and route tickets effectively'
            }
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label>Name *</Label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="e.g., London Office, IT Department, Finance Team"
            />
          </div>

          <div>
            <Label>Code</Label>
            <Input
              value={formData.code}
              onChange={(e) => setFormData({...formData, code: e.target.value})}
              placeholder="e.g., LON-001, IT-DEPT, FIN-TEAM"
            />
          </div>

          <div>
            <Label>Type *</Label>
            <Select value={formData.type} onValueChange={(value) => setFormData({...formData, type: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {businessUnitTypes.map(type => (
                  <SelectItem key={type} value={type}>
                    <span className="flex items-center">
                      <span className="mr-2">
                        {type === 'Geography' ? '🌍' :
                         type === 'Technical' ? '⚙️' :
                         type === 'Business Support' ? '💼' : '📁'}
                      </span>
                      {type}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Status</Label>
            <Select value={formData.status} onValueChange={(value) => setFormData({...formData, status: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Active">✅ Active</SelectItem>
                <SelectItem value="Inactive">⏸️ Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Description</Label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Brief description of this business unit's purpose and scope..."
              rows={3}
            />
          </div>
        </div>

        <div className="flex justify-end space-x-2 pt-4">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button 
            onClick={handleSubmit}
            className="bg-emerald-600 hover:bg-emerald-700"
            disabled={!formData.name.trim()}
          >
            {unit ? 'Update Unit' : 'Create Unit'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
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
            <Route path="/boost" element={<BoostSupport />} />
            <Route path="/boost/admin" element={<BoostAdmin />} />
            <Route path="/tickets" element={<TicketManagement />} />
            <Route path="/documents" element={<DocumentManagement />} />
            <Route path="/admin" element={<SystemAdmin />} />
          </Routes>
        </main>
        <Toaster />
      </BrowserRouter>
    </div>
  );
}

export default App;