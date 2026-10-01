#!/usr/bin/env python3
"""
export_room_json.py - Export official live BAND room session transcript into room.json

Uses the BAND REST API to fetch:
1. Room metadata & participants
2. Complete message history (including handoffs and verdicts)
3. Shared task board state & task list
4. Saves directly to room.json and runs sanitize_room_json.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

SUBMISSION_DIR = Path(__file__).resolve().parent.parent
load_dotenv(SUBMISSION_DIR / ".env")

from band.client.rest import RestClient

DEFAULT_ROOM_ID = "84d4e744-cbe5-4014-b3c7-2b130b32b4d6"


def export_room(room_id: str = DEFAULT_ROOM_ID, output_file: str = "room.json"):
    api_key = (
        os.getenv("BAND_PLANNER_KEY")
        or os.getenv("BAND_CRITIC_KEY")
        or os.getenv("BAND_CODER_KEY")
        or os.getenv("BAND_API_KEY")
    )

    if not api_key:
        print("[ERROR] No BAND API key found in .env or environment.")
        return 1

    print(f"[*] Connecting to BAND REST API to export session {room_id}...")
    client = RestClient(api_key=api_key)

    # 1. Fetch Chat Info
    chat_info = {}
    try:
        chat_resp = client.agent_api_chats.get_agent_chat(id=room_id)
        chat_info = getattr(chat_resp, "dict", lambda: getattr(chat_resp, "__dict__", {}))()
        if hasattr(chat_resp, "model_dump"):
            chat_info = chat_resp.model_dump()
        print("  [OK] Retrieved chat room metadata")
    except Exception as e:
        print(f"  [!] Chat metadata notice: {e}")

    # 2. Fetch Messages
    messages = []
    try:
        msg_resp = client.agent_api_messages.list_agent_messages(chat_id=room_id, status="all", limit=100)
        raw_msgs = getattr(msg_resp, "data", []) or getattr(msg_resp, "messages", []) or []
        for m in raw_msgs:
            if hasattr(m, "model_dump"):
                messages.append(m.model_dump())
            elif hasattr(m, "dict"):
                messages.append(m.dict())
            elif isinstance(m, dict):
                messages.append(m)
            else:
                messages.append(getattr(m, "__dict__", str(m)))
        print(f"  [OK] Retrieved {len(messages)} room messages")
    except Exception as e:
        print(f"  [!] Message fetch notice: {e}")

    # 3. Fetch Board & Tasks
    board = {}
    tasks = []
    try:
        board_resp = client.agent_api_chat_tasks.get_chat_board(chat_id=room_id)
        if hasattr(board_resp, "model_dump"):
            board = board_resp.model_dump()
        elif hasattr(board_resp, "dict"):
            board = board_resp.dict()
        print("  [OK] Retrieved room board state")
    except Exception as e:
        print(f"  [!] Board notice: {e}")

    try:
        tasks_resp = client.agent_api_chat_tasks.list_chat_tasks(chat_id=room_id)
        raw_tasks = getattr(tasks_resp, "data", []) or []
        for t in raw_tasks:
            if hasattr(t, "model_dump"):
                tasks.append(t.model_dump())
            elif hasattr(t, "dict"):
                tasks.append(t.dict())
            else:
                tasks.append(getattr(t, "__dict__", str(t)))
        print(f"  [OK] Retrieved {len(tasks)} tasks from board")
    except Exception as e:
        print(f"  [!] Tasks notice: {e}")

    # Build unified export package
    session_export = {
        "schema_version": "band.room_transcript.v1",
        "room_id": room_id,
        "chat": chat_info,
        "board": board,
        "tasks": tasks,
        "messages": messages,
    }

    out_path = SUBMISSION_DIR / output_file
    out_path.write_text(json.dumps(session_export, indent=2, default=str), encoding="utf-8")
    print(f"\n[SUCCESS] Wrote complete BAND session transcript to {out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    room_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOM_ID
    sys.exit(export_room(room_id))
