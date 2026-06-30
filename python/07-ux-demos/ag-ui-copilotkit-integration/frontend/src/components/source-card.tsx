// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { FileText, ChevronDown, ChevronUp } from "lucide-react";

interface Source {
  id: string;
  name: string;
  title: string;
  type: string;
  content: string;
  metadata: {
    score: number;
    sections: string[];
  };
}

interface SourceCardProps {
  source: Source;
  index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className={cn(
        "group p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700",
        "shadow-sm hover:shadow-md transition-all duration-200",
        "hover:border-indigo-300 dark:hover:border-indigo-600"
      )}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
          <FileText className="w-5 h-5 text-white" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h4 className="text-sm font-semibold text-gray-800 dark:text-gray-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                {source.title}
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {source.name}
              </p>
            </div>
            {source.metadata.score > 0 && (
              <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                {Math.round(source.metadata.score * 100)}% match
              </span>
            )}
          </div>

          {/* Content Preview */}
          <p
            className={cn(
              "text-sm text-gray-600 dark:text-gray-400 mt-2 leading-relaxed",
              !isExpanded && "line-clamp-2"
            )}
          >
            {source.content}
          </p>

          {/* Sections */}
          {source.metadata.sections.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {source.metadata.sections.slice(0, 3).map((section, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
                >
                  {section}
                </span>
              ))}
            </div>
          )}

          {/* Expand/Collapse */}
          {source.content.length > 150 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1 text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium mt-2"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-3 h-3" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="w-3 h-3" />
                  Show more
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface SearchResultsProps {
  status: "inProgress" | "executing" | "complete" | "error";
  query?: string;
  result?: string;
}

export function SearchResults({ status, query, result }: SearchResultsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Loading state
  if (status === "inProgress" || status === "executing") {
    return (
      <div className="my-4 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-gradient-to-br from-indigo-50 to-white dark:from-indigo-950/50 dark:to-gray-900 p-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center animate-pulse">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
              Searching Knowledge Base
            </h3>
            {query && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Query: &quot;{query}&quot;
              </p>
            )}
          </div>
        </div>
        <div className="mt-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                  <div className="h-3 bg-gray-100 dark:bg-gray-700/50 rounded w-full" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Parse result
  let data: { sources: Source[]; summary?: string } = { sources: [] };
  try {
    if (result) {
      data = typeof result === "string" ? JSON.parse(result) : result;
    }
  } catch {
    return (
      <div className="my-4 p-4 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30">
        <p className="text-sm text-red-600 dark:text-red-400">Failed to parse search results</p>
      </div>
    );
  }

  // Empty state
  if (!data.sources || data.sources.length === 0) {
    return (
      <div className="my-4 p-6 rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 text-center">
        <p className="text-sm text-amber-700 dark:text-amber-400">
          No results found{query && <> for &quot;{query}&quot;</>}
        </p>
      </div>
    );
  }

  // Results - collapsed by default
  return (
    <div className="my-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-900 overflow-hidden">
      {/* Header - clickable to expand/collapse */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-900/80 hover:bg-gray-50 dark:hover:bg-gray-800/80 transition-colors"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-left">
              <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                Knowledge Base Results
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Found {data.sources.length} source{data.sources.length !== 1 ? "s" : ""}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
              ✓ Complete
            </span>
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
      </button>

      {/* Results - only shown when expanded */}
      {isExpanded && (
        <div className="p-4 space-y-3">
          {data.sources.map((source, index) => (
            <SourceCard key={source.id} source={source} index={index} />
          ))}
        </div>
      )}
    </div>
  );
}
