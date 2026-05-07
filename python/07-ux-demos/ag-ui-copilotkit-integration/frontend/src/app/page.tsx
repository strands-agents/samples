// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  CopilotKit,
  useCopilotAction,
  useCoAgent,
} from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { QuizCard } from "@/components/quiz-card";
import { SearchResults } from "@/components/source-card";

// ============================================
// Types
// ============================================
type QuizState = {
  question: string;
  options: string[];
  correctIndex: number;
  selectedIndex: number | null;
  answered: boolean;
  resolve: ((result: string) => void) | null;
};

type ChecklistItem = {
  id: string;
  task: string;
  completed: boolean;
};

type AgentState = {
  checklist?: ChecklistItem[];
  topic?: string;
};

// ============================================
// Checklist Panel Component
// ============================================
function ChecklistPanel({ 
  checklist, 
  topic, 
  onToggle,
  isCollapsed,
  onToggleCollapse,
}: { 
  checklist: ChecklistItem[]; 
  topic: string;
  onToggle: (id: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}) {
  const completedCount = checklist.filter(item => item.completed).length;
  const progress = checklist.length > 0 ? (completedCount / checklist.length) * 100 : 0;

  // Collapsed state - show just a small button
  if (isCollapsed) {
    return (
      <div className="flex-shrink-0 border-r border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
        <button
          onClick={onToggleCollapse}
          className="w-12 h-full flex flex-col items-center justify-center gap-2 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          title="Expand checklist"
        >
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          <span className="text-xs font-medium text-slate-600 dark:text-slate-400 writing-mode-vertical" style={{ writingMode: 'vertical-rl' }}>
            {completedCount}/{checklist.length}
          </span>
          <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div className="w-80 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 flex flex-col h-full shadow-lg">
      {/* Gradient Header - matching quiz card style */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 text-white/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            <span className="text-xs font-semibold text-white/90 uppercase tracking-wider">
              Learning Checklist
            </span>
          </div>
          <div className="flex items-center gap-2">
            {/* Shared State Indicator */}
            <div className="flex items-center gap-1 px-2 py-0.5 bg-white/20 rounded-full">
              <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-xs text-white/90 font-medium">Synced</span>
            </div>
            {/* Collapse Button */}
            <button
              onClick={onToggleCollapse}
              className="p-1 hover:bg-white/20 rounded transition-colors"
              title="Collapse sidebar"
            >
              <svg className="w-4 h-4 text-white/80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Topic and Progress */}
      <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800">
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100 mb-3">
          {topic}
        </h3>
        <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-300" 
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
          {completedCount} of {checklist.length} completed
        </p>
      </div>

      {/* Checklist Items */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {checklist.map((item, index) => {
          const letter = String.fromCharCode(65 + index);
          return (
            <button
              key={item.id}
              onClick={() => onToggle(item.id)}
              className={`w-full flex items-center gap-3 p-3 rounded-lg border-2 text-left transition-all duration-200 ${
                item.completed 
                  ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-950/30" 
                  : "border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500 hover:bg-slate-50 dark:hover:bg-slate-800/50"
              }`}
            >
              <span
                className={`flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold transition-colors ${
                  item.completed 
                    ? "bg-emerald-500 text-white" 
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                }`}
              >
                {item.completed ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  letter
                )}
              </span>
              <span className={`flex-1 text-sm font-medium ${
                item.completed 
                  ? "text-emerald-800 dark:text-emerald-200 line-through" 
                  : "text-slate-700 dark:text-slate-300"
              }`}>
                {item.task}
              </span>
            </button>
          );
        })}
      </div>

      {/* Footer hint */}
      <div className="px-5 py-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
        <p className="text-xs text-center text-slate-500 dark:text-slate-400">
          Try asking: &quot;How am I doing on my checklist?&quot;
        </p>
      </div>
    </div>
  );
}

// ============================================
// Main Chat Component
// ============================================
function ChatPage() {
  // Toast notification state
  const [toast, setToast] = useState<{ message: string; type: string } | null>(null);
  
  // Quiz states
  const [quizStates, setQuizStates] = useState<Map<string, QuizState>>(new Map());
  // Ref kept in sync so the render() closure always reads current state (avoids stale closure on tool-result renders)
  const quizStatesRef = useRef(quizStates);
  useEffect(() => {
    quizStatesRef.current = quizStates;
  }, [quizStates]);

  // Sidebar collapsed state
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // ============================================
  // SHARED STATE - useCoAgent for bidirectional state sync
  // ============================================
  const { state, setState } = useCoAgent<AgentState>({
    name: "strands_agent",
    initialState: {
      checklist: [],
      topic: "",
    },
  });

  // Handle checklist item toggle (frontend -> agent state sync)
  const handleChecklistToggle = useCallback((itemId: string) => {
    if (!state.checklist) return;
    
    const updatedChecklist = state.checklist.map(item =>
      item.id === itemId ? { ...item, completed: !item.completed } : item
    );
    
    setState({
      ...state,
      checklist: updatedChecklist,
    });
  }, [state, setState]);

  // Auto-hide toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  // ============================================
  // GENERATIVE UI - Tool Rendering with useCopilotAction
  // ============================================
  
  // Render search_knowledge tool results
  useCopilotAction({
    name: "search_knowledge",
    description: "Search the knowledge base for information about AgentCore",
    parameters: [
      { name: "query", type: "string", description: "Search query", required: true },
    ],
    available: "disabled", // Agent-side tool, just render results
    render: ({ status, args, result }) => (
      <SearchResults status={status as "inProgress" | "executing" | "complete"} query={args?.query} result={result} />
    ),
  });

  // Render update_learning_checklist tool results (inline notification)
  useCopilotAction({
    name: "update_learning_checklist",
    description: "Create a learning checklist",
    parameters: [
      { name: "topic", type: "string", description: "Learning topic", required: true },
      { name: "tasks", type: "string", description: "JSON array of tasks", required: true },
    ],
    available: "disabled",
    render: ({ status, args }) => {
      if (status === "inProgress") {
        return (
          <div className="my-2 p-4 bg-indigo-50 dark:bg-indigo-950/30 rounded-lg border border-indigo-200 dark:border-indigo-800">
            <div className="flex items-center gap-2">
              <div className="animate-spin h-4 w-4 border-2 border-indigo-600 border-t-transparent rounded-full" />
              <span className="text-indigo-700 dark:text-indigo-300 font-medium">Creating learning checklist...</span>
            </div>
          </div>
        );
      }
      
      return (
        <div className="my-2 p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-green-700 dark:text-green-300 font-medium">
              Checklist created: {args?.topic}
            </span>
          </div>
          <p className="text-sm text-green-600 dark:text-green-400 mt-1 ml-7">
            Check the sidebar panel to track your progress!
          </p>
        </div>
      );
    },
  });

  // ============================================
  // FRONTEND TOOL - show_notification
  // ============================================
  useCopilotAction({
    name: "show_notification",
    description: "Show a toast notification to the user. Use for confirmations, tips, or alerts.",
    parameters: [
      { name: "message", type: "string", description: "The notification message", required: true },
      { name: "type", type: "string", description: "Type: 'success', 'info', 'warning', 'error'", required: false },
    ],
    handler: async ({ message, type = "info" }) => {
      setToast({ message, type });
      return `Notification shown: "${message}"`;
    },
    render: ({ status, args }) => {
      if (status === "inProgress") {
        return <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm text-gray-600 dark:text-gray-400">Preparing notification...</div>;
      }
      return <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm text-gray-600 dark:text-gray-400">✓ Notification: &quot;{args?.message}&quot;</div>;
    },
  });

  // ============================================
  // FRONTEND TOOL - show_quiz_question
  // ============================================
  const handleQuizAnswer = useCallback((quizId: string, selectedIndex: number) => {
    setQuizStates((prev: Map<string, QuizState>) => {
      const newMap = new Map(prev);
      const quiz = newMap.get(quizId);
      if (quiz && !quiz.answered) {
        const updatedQuiz = { ...quiz, selectedIndex, answered: true };
        newMap.set(quizId, updatedQuiz);
        
        if (quiz.resolve) {
          const isCorrect = selectedIndex === quiz.correctIndex;
          quiz.resolve(JSON.stringify({
            question: quiz.question,
            selectedAnswer: quiz.options[selectedIndex],
            correctAnswer: quiz.options[quiz.correctIndex],
            isCorrect,
          }));
        }
      }
      return newMap;
    });
  }, []);

  useCopilotAction({
    name: "show_quiz_question",
    description: "Display an interactive quiz question. Returns the user's answer.",
    parameters: [
      { name: "question", type: "string", description: "The quiz question", required: true },
      { name: "options", type: "string", description: "JSON array of 4 answer options", required: true },
      { name: "correctIndex", type: "number", description: "Index of correct answer (0-3)", required: true },
    ],
    handler: async ({ question, options, correctIndex }) => {
      let parsedOptions: string[];
      try {
        parsedOptions = typeof options === "string" ? JSON.parse(options) : options;
      } catch {
        return JSON.stringify({ error: "Invalid options format" });
      }

      // Deterministic quiz ID derived from the question so handler and render agree
      const quizId = `quiz_${question.substring(0, 40)}`;

      return new Promise<string>((resolve) => {
        setQuizStates((prev: Map<string, QuizState>) => {
          const newMap = new Map(prev);
          newMap.set(quizId, {
            question,
            options: parsedOptions,
            correctIndex: Number(correctIndex),
            selectedIndex: null,
            answered: false,
            resolve,
          });
          return newMap;
        });
      });
    },
    render: ({ status, args, result }) => {
      // Same deterministic ID scheme as the handler
      const quizId = `quiz_${args?.question?.substring(0, 40)}`;
      // Read via ref so this render always sees the latest quizStates,
      // even when CopilotKit re-renders after the handler has updated state
      const quiz = quizStatesRef.current.get(quizId);

      let displayOptions: string[] = [];
      try {
        displayOptions = typeof args?.options === "string" ? JSON.parse(args.options) : (args?.options || []);
      } catch {
        displayOptions = [];
      }

      if (status === "inProgress" && !quiz) {
        return <QuizCard question="" options={[]} correctIndex={0} selectedIndex={null} isAnswered={false} onAnswer={() => {}} isLoading={true} />;
      }

      let resultData: { selectedIndex?: number } = {};
      if (result) {
        try { resultData = JSON.parse(result); } catch {}
      }

      return (
        <QuizCard
          question={args?.question || ""}
          options={displayOptions}
          correctIndex={Number(args?.correctIndex)}
          selectedIndex={quiz?.selectedIndex ?? resultData.selectedIndex ?? null}
          isAnswered={quiz?.answered || resultData.selectedIndex !== undefined}
          onAnswer={(index) => handleQuizAnswer(quizId, index)}
        />
      );
    },
  });

  // Check if we have a checklist to show
  const hasChecklist = state.checklist && state.checklist.length > 0;

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-gray-50 dark:bg-gray-950">
      {/* Title Bar - AWS Console style */}
      <header className="flex-shrink-0 h-12 bg-[#232f3e] flex items-center px-4">
        <div className="flex items-center gap-3">
          {/* Logo */}
          <div className="w-7 h-7 rounded bg-gradient-to-br from-orange-400 to-orange-500 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-white">
            AnyCompany Learning
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Checklist Sidebar - SHARED STATE rendered outside chat */}
        {hasChecklist && (
          <ChecklistPanel 
            checklist={state.checklist!} 
            topic={state.topic || "Learning Plan"}
            onToggle={handleChecklistToggle}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          />
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Toast Notification */}
        {toast && (
          <div className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg border transition-all ${
            toast.type === "success" ? "bg-green-50 border-green-200 text-green-800" :
            toast.type === "warning" ? "bg-yellow-50 border-yellow-200 text-yellow-800" :
            toast.type === "error" ? "bg-red-50 border-red-200 text-red-800" :
            "bg-blue-50 border-blue-200 text-blue-800"
          }`}>
            <div className="flex items-center gap-3">
              <span className="font-medium">{toast.message}</span>
              <button onClick={() => setToast(null)} className="opacity-50 hover:opacity-100">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden pb-4">
          <CopilotChat
            labels={{
              title: "AgentCore Assistant",
              initial: "Hi! I'm your AgentCore documentation assistant. Ask me about deploying agents, concepts, or best practices. I can also quiz you on what you've learned!",
            }}
            className="h-full"
          />
        </div>
        </div>
      </div>
    </div>
  );
}

// ============================================
// Root Component with CopilotKit Provider
// ============================================
export default function Home() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="strands_agent">
      <ChatPage />
    </CopilotKit>
  );
}
