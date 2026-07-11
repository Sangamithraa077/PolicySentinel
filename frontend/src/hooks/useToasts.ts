import { useCallback, useRef, useState } from "react";

import type { ToastMessage } from "@/components/common/Toast";

export function useToasts(autoDismissMs = 5000) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const nextId = useRef(1);
  const timers = useRef(new Map<number, ReturnType<typeof setTimeout>>());

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const push = useCallback(
    (tone: ToastMessage["tone"], text: string) => {
      const id = nextId.current++;
      setToasts((current) => [...current, { id, tone, text }]);
      timers.current.set(
        id,
        setTimeout(() => dismiss(id), autoDismissMs),
      );
    },
    [autoDismissMs, dismiss],
  );

  return { toasts, push, dismiss };
}
