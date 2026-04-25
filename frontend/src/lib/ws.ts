"use client";

import { useEffect } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import {
  listAgents,
  listApprovals,
  listAudit,
  listEvals,
  listPolicies,
} from "./api";
import { useAppStore } from "./store";
import type { StreamFrame } from "./types";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/v1/stream";

async function rehydrateFromRest() {
  const { rehydrate } = useAppStore.getState();
  try {
    const [audit, approvals, agents, policies, evals] = await Promise.all([
      listAudit({ limit: 100 }),
      listApprovals("pending"),
      listAgents(),
      listPolicies(),
      listEvals(),
    ]);
    const latestPolicy =
      policies
        .filter((p) => p.status === "published")
        .sort((a, b) =>
          (b.published_at ?? "").localeCompare(a.published_at ?? ""),
        )[0] ?? null;
    rehydrate({ audit, approvals, agents, evals, latestPolicy });
  } catch (err) {
    console.error("[ws] rehydrate failed", err);
  }
}

export function useAppStream() {
  const applyFrame = useAppStore((s) => s.applyFrame);
  const setConnection = useAppStore((s) => s.setConnection);

  const { readyState, lastMessage } = useWebSocket(WS_URL, {
    shouldReconnect: () => true,
    reconnectAttempts: 1000,
    reconnectInterval: 2000,
    onOpen: () => {
      setConnection("connected");
      void rehydrateFromRest();
    },
    onClose: () => setConnection("disconnected"),
    onError: () => setConnection("disconnected"),
  });

  useEffect(() => {
    if (!lastMessage) return;
    try {
      const frame = JSON.parse(lastMessage.data) as StreamFrame;
      applyFrame(frame);
    } catch (err) {
      console.error("[ws] bad frame", err, lastMessage.data);
    }
  }, [lastMessage, applyFrame]);

  useEffect(() => {
    if (readyState === ReadyState.CONNECTING) {
      setConnection("connecting");
    }
  }, [readyState, setConnection]);

  return readyState;
}
