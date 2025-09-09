// Type definitions for the matching system

export interface Candidate {
  bachelor_major: string;
  gpa_scale: string;
  gpa_value: number;
  ielts_overall: number;
  ielts_subscores?: {
    listening: number;
    reading: number;
    writing: number;
    speaking: number;
  };
  work_years?: number;
  interests: string[];
  city_pref: string[];
  budget_nzd_per_year?: number;
}

export interface DetailedScores {
  academic_fit: number;
  english_proficiency: number;
  field_alignment: number;
  location_preference: number;
  budget_compatibility: number;
}

export interface MatchReasoning {
  academic_fit?: string;
  english_proficiency?: string;
  field_alignment?: string;
  location_preference?: string;
  budget_compatibility?: string;
  overall_assessment?: string;
}

export interface MatchResult {
  program?: string;
  program_name?: string;
  university: string;
  score?: number;
  overall_score?: number;
  detailed_scores?: DetailedScores;
  reasoning?: string | MatchReasoning;
  strengths?: string[];
  red_flags?: string[];
  url?: string;
  program_url?: string;
  eligible?: boolean;
  rejection_reason?: string;
}

export interface AllMatchResults {
  eligible_matches: MatchResult[];
  rejected_matches: MatchResult[];
  total_evaluated: number;
}
