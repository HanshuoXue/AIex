"use client";

import { useState } from "react";

interface CandidateFormProps {
  onMatch: (data: any) => void;
  onDetailedMatch: (data: any) => void;
  onAllMatch: (data: any) => void;
  loading: boolean;
}

export default function CandidateForm({
  onMatch,
  onDetailedMatch,
  onAllMatch,
  loading,
}: CandidateFormProps) {
  const [formData, setFormData] = useState({
    bachelor_major: "computer science",
    gpa_scale: "4.0",
    gpa_value: 3.5,
    ielts_overall: 7.0,
    ielts_subscores: {
      listening: 7.0,
      reading: 7.0,
      writing: 6.5,
      speaking: 7.0,
    },
    work_years: 1,
    interests: ["artificial intelligence", "machine learning"],
    city_pref: ["Wellington", "Auckland"],
    budget_nzd_per_year: 60000,
  });

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleArrayChange = (field: string, value: string) => {
    const items = value
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item);
    setFormData((prev) => ({
      ...prev,
      [field]: items,
    }));
  };

  const handleIeltsChange = (skill: string, value: number) => {
    setFormData((prev) => ({
      ...prev,
      ielts_subscores: {
        ...prev.ielts_subscores,
        [skill]: value,
      },
    }));
  };

  const handleSubmit = (e: React.FormEvent, isDetailed = false) => {
    e.preventDefault();
    if (isDetailed) {
      onDetailedMatch(formData);
    } else {
      onMatch(formData);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        📋 Candidate Information
      </h2>

      <form className="space-y-4">
        {/* Academic background */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-700 mb-3">
            🎓 Academic Background
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Bachelor's Major
              </label>
              <input
                type="text"
                value={formData.bachelor_major}
                onChange={(e) => handleChange("bachelor_major", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="computer science"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                GPA ({formData.gpa_scale} scale)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="4"
                value={formData.gpa_value}
                onChange={(e) =>
                  handleChange("gpa_value", parseFloat(e.target.value))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* English proficiency */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-700 mb-3">
            🗣️ English Proficiency
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                IELTS Overall
              </label>
              <input
                type="number"
                step="0.5"
                min="0"
                max="9"
                value={formData.ielts_overall}
                onChange={(e) =>
                  handleChange("ielts_overall", parseFloat(e.target.value))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {Object.entries(formData.ielts_subscores).map(([skill, score]) => (
              <div key={skill}>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  {skill === "listening"
                    ? "Listening"
                    : skill === "reading"
                    ? "Reading"
                    : skill === "writing"
                    ? "Writing"
                    : "Speaking"}
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="9"
                  value={score}
                  onChange={(e) =>
                    handleIeltsChange(skill, parseFloat(e.target.value))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Personal preferences */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-700 mb-3">
            💡 Personal Preferences
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Work Experience (years)
              </label>
              <input
                type="number"
                min="0"
                value={formData.work_years}
                onChange={(e) =>
                  handleChange("work_years", parseInt(e.target.value))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Interest Areas (comma separated)
              </label>
              <input
                type="text"
                value={formData.interests.join(", ")}
                onChange={(e) => handleArrayChange("interests", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="artificial intelligence, machine learning"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                City Preferences (comma separated)
              </label>
              <input
                type="text"
                value={formData.city_pref.join(", ")}
                onChange={(e) => handleArrayChange("city_pref", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Wellington, Auckland"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Annual Budget (NZD)
              </label>
              <input
                type="number"
                min="0"
                step="1000"
                value={formData.budget_nzd_per_year}
                onChange={(e) =>
                  handleChange("budget_nzd_per_year", parseInt(e.target.value))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Quick template buttons */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-700 mb-3">
            ⚡ Quick Test Templates
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => {
                setFormData({
                  bachelor_major: "computer science",
                  gpa_scale: "4.0",
                  gpa_value: 3.7,
                  ielts_overall: 7.5,
                  ielts_subscores: {
                    listening: 8.0,
                    reading: 7.5,
                    writing: 7.0,
                    speaking: 7.5,
                  },
                  work_years: 2,
                  interests: [
                    "artificial intelligence",
                    "machine learning",
                    "data science",
                  ],
                  city_pref: ["Wellington"],
                  budget_nzd_per_year: 70000,
                });
              }}
              className="bg-green-100 text-green-800 py-2 px-4 rounded-lg font-medium hover:bg-green-200 transition-colors duration-200 text-sm"
            >
              💻 Computer Science Template
              <div className="text-xs mt-1 opacity-75">
                High GPA • High IELTS • AI Interest • Sufficient Budget
              </div>
            </button>

            <button
              type="button"
              onClick={() => {
                setFormData({
                  bachelor_major: "business administration",
                  gpa_scale: "4.0",
                  gpa_value: 3.2,
                  ielts_overall: 6.5,
                  ielts_subscores: {
                    listening: 6.5,
                    reading: 7.0,
                    writing: 6.0,
                    speaking: 6.5,
                  },
                  work_years: 0,
                  interests: ["business management", "marketing"],
                  city_pref: ["Auckland"],
                  budget_nzd_per_year: 45000,
                });
              }}
              className="bg-blue-100 text-blue-800 py-2 px-4 rounded-lg font-medium hover:bg-blue-200 transition-colors duration-200 text-sm"
            >
              📊 Business Management Template
              <div className="text-xs mt-1 opacity-75">
                Medium GPA • Standard IELTS • Business Background • Limited
                Budget
              </div>
            </button>
          </div>
        </div>

        {/* Submit buttons */}
        <div className="space-y-3 pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={(e) => handleSubmit(e, false)}
              disabled={loading}
              className="bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {loading ? "Matching..." : "🚀 Quick Match"}
            </button>

            <button
              type="button"
              onClick={(e) => handleSubmit(e, true)}
              disabled={loading}
              className="bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {loading ? "Analyzing..." : "📊 Detailed Analysis"}
            </button>
          </div>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              onAllMatch(formData);
            }}
            disabled={loading}
            className="w-full bg-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {loading
              ? "Full analysis..."
              : "🔍 Complete Analysis (including rejected programs)"}
          </button>
        </div>
      </form>
    </div>
  );
}
