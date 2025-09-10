"use client";

import type { MatchResult, AllMatchResults } from "../../types";

interface MatchResultsProps {
  results: MatchResult[] | AllMatchResults | null;
  loading: boolean;
}

export default function MatchResults({ results, loading }: MatchResultsProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg h-full flex flex-col">
        <div className="p-6 pb-3 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-800">🔍 Match Results</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <span className="text-base text-gray-600">
              AI is analyzing match compatibility...
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="bg-white rounded-xl shadow-lg h-full flex flex-col">
        <div className="p-6 pb-3 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-800">🔍 Match Results</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="text-5xl mb-4">🎯</div>
            <p className="text-base mb-2">
              Click match button to start intelligent analysis
            </p>
            <p className="text-sm">
              We will recommend the most suitable programs based on your
              background
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Handle new data format (containing eligible and rejected)
  const isAllMatchFormat =
    results && typeof results === "object" && "eligible_matches" in results;
  const eligibleResults = isAllMatchFormat
    ? (results as AllMatchResults).eligible_matches
    : (results as MatchResult[]);
  const rejectedResults = isAllMatchFormat
    ? (results as AllMatchResults).rejected_matches
    : [];

  if (
    Array.isArray(eligibleResults) &&
    eligibleResults.length === 0 &&
    rejectedResults.length === 0
  ) {
    return (
      <div className="bg-white rounded-xl shadow-lg h-full flex flex-col">
        <div className="p-6 pb-3 border-b border-gray-100">
          <h2 className="text-xl font-bold text-gray-800">🔍 Match Results</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="text-5xl mb-4">😔</div>
            <p className="text-base mb-2">No matching programs found</p>
            <p className="text-sm">
              Please try adjusting your criteria or budget
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg flex flex-col h-full">
      <div className="p-6 pb-3 border-b border-gray-100">
        <h2 className="text-xl font-bold text-gray-800">
          🔍 Match Results{" "}
          <span className="text-sm font-normal text-gray-500">
            {isAllMatchFormat
              ? `(${eligibleResults.length} selected / ${rejectedResults.length} rejected)`
              : `(${eligibleResults.length} results)`}
          </span>
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-6 pt-4">
        <div className="space-y-6">
          {/* Selected Programs */}
          {eligibleResults.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-green-700 mb-4 flex items-center">
                ✅ Recommended Programs ({eligibleResults.length})
              </h3>
              <div className="space-y-4">
                {eligibleResults.map((result: MatchResult, index: number) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow duration-200"
                  >
                    {/* Program header info */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-gray-800 mb-1">
                          {result.program || result.program_name}
                        </h3>
                        <p className="text-gray-600 mb-2">
                          {result.university}
                        </p>

                        {/* Official link */}
                        {(result.url || result.program_url) && (
                          <a
                            href={result.url || result.program_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors duration-200 mb-2"
                          >
                            <span className="mr-1">🔗</span>
                            View Official Page
                            <svg
                              className="w-3 h-3 ml-1"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                              />
                            </svg>
                          </a>
                        )}

                        {/* Match score */}
                        <div className="flex items-center space-x-4">
                          <div className="flex items-center">
                            <span className="text-2xl font-bold text-blue-600">
                              {result.score || result.overall_score}
                            </span>
                            <span className="text-gray-500 ml-1">/100</span>
                          </div>

                          {/* Score bar */}
                          <div className="flex-1 bg-gray-200 rounded-full h-3">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500"
                              style={{
                                width: `${
                                  result.score || result.overall_score || 0
                                }%`,
                              }}
                            ></div>
                          </div>

                          {/* Match level */}
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              (result.score || result.overall_score || 0) >= 90
                                ? "bg-green-100 text-green-800"
                                : (result.score || result.overall_score || 0) >=
                                  80
                                ? "bg-blue-100 text-blue-800"
                                : (result.score || result.overall_score || 0) >=
                                  70
                                ? "bg-yellow-100 text-yellow-800"
                                : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {(result.score || result.overall_score || 0) >= 90
                              ? "🌟 Perfect Match"
                              : (result.score || result.overall_score || 0) >=
                                80
                              ? "✨ Excellent Match"
                              : (result.score || result.overall_score || 0) >=
                                70
                              ? "👍 Good Match"
                              : "🤔 Fair Match"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Detailed scores (if available) */}
                    {result.detailed_scores && (
                      <div className="mb-4">
                        <h4 className="font-semibold text-gray-700 mb-2">
                          📊 Detailed Scores
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                          {Object.entries(result.detailed_scores).map(
                            ([key, value]) => (
                              <div
                                key={key}
                                className="bg-gray-50 p-3 rounded-md"
                              >
                                <div className="text-xs text-gray-600 mb-1">
                                  {key === "academic_fit"
                                    ? "🎓 Academic Fit"
                                    : key === "english_proficiency"
                                    ? "🗣️ English Proficiency"
                                    : key === "field_alignment"
                                    ? "💡 Interest Match"
                                    : key === "location_preference"
                                    ? "📍 Location Preference"
                                    : key === "budget_compatibility"
                                    ? "💰 Budget Compatibility"
                                    : key}
                                </div>
                                <div className="font-semibold text-gray-800">
                                  {String(value)}
                                  <span className="text-xs text-gray-500 ml-1">
                                    /
                                    {key === "academic_fit"
                                      ? "35"
                                      : key === "english_proficiency"
                                      ? "25"
                                      : key === "field_alignment"
                                      ? "20"
                                      : key === "location_preference"
                                      ? "10"
                                      : key === "budget_compatibility"
                                      ? "10"
                                      : "100"}
                                  </span>
                                </div>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}

                    {/* Strengths and Concerns */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      {result.strengths && result.strengths.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-green-700 mb-2">
                            ✅ Strengths
                          </h4>
                          <ul className="space-y-1">
                            {result.strengths.map(
                              (strength: string, i: number) => (
                                <li
                                  key={i}
                                  className="text-sm text-green-600 flex items-start"
                                >
                                  <span className="mr-2">•</span>
                                  <span>{strength}</span>
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      )}

                      {result.red_flags && result.red_flags.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-orange-700 mb-2">
                            ⚠️ Concerns
                          </h4>
                          <ul className="space-y-1">
                            {result.red_flags.map((flag: string, i: number) => (
                              <li
                                key={i}
                                className="text-sm text-orange-600 flex items-start"
                              >
                                <span className="mr-2">•</span>
                                <span>{flag}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* AI Evaluation reasoning */}
                    {result.reasoning && (
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <h4 className="font-semibold text-blue-800 mb-2">
                          🤖 AI Analysis
                        </h4>

                        {typeof result.reasoning === "string" ? (
                          <p className="text-sm text-blue-700">
                            {result.reasoning}
                          </p>
                        ) : result.reasoning.overall_assessment ? (
                          <p className="text-sm text-blue-700">
                            {result.reasoning.overall_assessment}
                          </p>
                        ) : (
                          <div className="space-y-2">
                            {result.reasoning.academic_fit && (
                              <p className="text-sm text-blue-700">
                                <span className="font-medium">
                                  🎓 Academic Fit：
                                </span>
                                {result.reasoning.academic_fit}
                              </p>
                            )}
                            {result.reasoning.field_alignment && (
                              <p className="text-sm text-blue-700">
                                <span className="font-medium">
                                  💡 Interest Match：
                                </span>
                                {result.reasoning.field_alignment}
                              </p>
                            )}
                            {result.reasoning.budget_compatibility && (
                              <p className="text-sm text-blue-700">
                                <span className="font-medium">
                                  💰 Budget Analysis:
                                </span>
                                {result.reasoning.budget_compatibility}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rejected Programs */}
          {rejectedResults.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-red-700 mb-4 flex items-center">
                ❌ Rejected Programs ({rejectedResults.length})
                <span className="text-sm font-normal text-gray-500 ml-2">
                  - View rejection reasons
                </span>
              </h3>
              <div className="space-y-4">
                {rejectedResults.map((result: MatchResult, index: number) => (
                  <div
                    key={`rejected-${index}`}
                    className="border border-red-200 rounded-lg p-5 bg-red-50 hover:shadow-md transition-shadow duration-200"
                  >
                    {/* Program header info */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h4 className="text-lg font-bold text-gray-800 mb-1">
                          {result.program_name}
                        </h4>
                        <p className="text-gray-600 mb-2">
                          {result.university}
                        </p>

                        {/* Official link */}
                        {result.program_url && (
                          <a
                            href={result.program_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors duration-200 mb-2"
                          >
                            <span className="mr-1">🔗</span>
                            View Official Page
                            <svg
                              className="w-3 h-3 ml-1"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                              />
                            </svg>
                          </a>
                        )}

                        {/* Score */}
                        <div className="flex items-center space-x-4">
                          <div className="flex items-center">
                            <span className="text-xl font-bold text-red-600">
                              {result.overall_score}
                            </span>
                            <span className="text-gray-500 ml-1">/100</span>
                          </div>

                          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                            ❌ Not Selected
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Rejection Reason */}
                    <div className="bg-red-100 p-4 rounded-lg">
                      <h4 className="font-semibold text-red-800 mb-2">
                        🚫 Rejection Reason
                      </h4>
                      <p className="text-sm text-red-700">
                        {result.rejection_reason ||
                          (typeof result.reasoning === "object"
                            ? result.reasoning?.overall_assessment
                            : result.reasoning) ||
                          "Failed AI evaluation screening"}
                      </p>
                    </div>

                    {/* Detailed Score (if available) */}
                    {result.detailed_scores && (
                      <div className="mt-4">
                        <h4 className="font-semibold text-gray-700 mb-2">
                          📊 Detailed Scores
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                          {Object.entries(result.detailed_scores).map(
                            ([key, value]) => (
                              <div
                                key={key}
                                className="bg-gray-100 p-3 rounded-md"
                              >
                                <div className="text-xs text-gray-600 mb-1">
                                  {key === "academic_fit"
                                    ? "🎓 Academic Fit"
                                    : key === "english_proficiency"
                                    ? "🗣️ English Proficiency"
                                    : key === "field_alignment"
                                    ? "💡 Interest Match"
                                    : key === "location_preference"
                                    ? "📍 Location Preference"
                                    : key === "budget_compatibility"
                                    ? "💰 Budget Compatibility"
                                    : key}
                                </div>
                                <div className="font-semibold text-gray-800">
                                  {String(value)}
                                  <span className="text-xs text-gray-500 ml-1">
                                    /
                                    {key === "academic_fit"
                                      ? "35"
                                      : key === "english_proficiency"
                                      ? "25"
                                      : key === "field_alignment"
                                      ? "20"
                                      : key === "location_preference"
                                      ? "10"
                                      : key === "budget_compatibility"
                                      ? "10"
                                      : "100"}
                                  </span>
                                </div>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom tip */}
      <div className="p-4 pt-2 border-t border-gray-100 bg-gray-50 rounded-b-xl">
        <p className="text-xs text-gray-600 text-center">
          💡 <strong>Tip:</strong>
          Match scores are based on comprehensive evaluation of academic
          background, English proficiency, interest alignment, location
          preference, and budget compatibility
        </p>
      </div>
    </div>
  );
}
