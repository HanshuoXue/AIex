"use client";

import { useState } from "react";
import CandidateForm from "./components/CandidateForm";
import MatchResults from "./components/MatchResults";
import type { Candidate, MatchResult, AllMatchResults } from "../types";

export default function Home() {
  const [results, setResults] = useState<
    MatchResult[] | AllMatchResults | null
  >(null);
  const [loading, setLoading] = useState(false);

  const handleMatch = async (candidateData: Candidate) => {
    setLoading(true);
    try {
      const response = await fetch("https://api-alex-12345.azurewebsites.net/match", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(candidateData),
      });

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Match failed:", error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleDetailedMatch = async (candidateData: Candidate) => {
    setLoading(true);
    try {
      const response = await fetch("https://api-alex-12345.azurewebsites.net/match/detailed", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(candidateData),
      });

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Detailed match failed:", error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAllMatch = async (candidateData: Candidate) => {
    setLoading(true);
    try {
      const response = await fetch("https://api-alex-12345.azurewebsites.net/match/all", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(candidateData),
      });

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Full analysis failed:", error);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
      <div className="container mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🎓 New Zealand Study Program Smart Matching System
          </h1>
          <p className="text-lg text-gray-600">
            AI-Powered Personalized Program Recommendation Platform
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <CandidateForm
              onMatch={handleMatch}
              onDetailedMatch={handleDetailedMatch}
              onAllMatch={handleAllMatch}
              loading={loading}
            />
          </div>

          <div>
            <MatchResults results={results} loading={loading} />
          </div>
        </div>
      </div>
    </main>
  );
}
