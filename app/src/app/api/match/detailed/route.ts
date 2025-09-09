import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL =
  process.env.API_BASE_URL || "https://api-alex-12345.azurewebsites.net";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${API_BASE_URL}/match/detailed`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Detailed API proxy error:", error);
    return NextResponse.json(
      {
        error:
          "Detailed analysis service is temporarily unavailable, please try again later",
      },
      { status: 500 }
    );
  }
}
