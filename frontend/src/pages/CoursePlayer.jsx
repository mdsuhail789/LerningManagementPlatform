import { ArrowLeft, ExternalLink, Play } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";

function extractYouTubeId(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    const host = u.hostname.replace(/^www\./, "").toLowerCase();

    // youtu.be/<id>
    if (host === "youtu.be") {
      const id = u.pathname.split("/").filter(Boolean)[0];
      return id || null;
    }

    // youtube.com/watch?v=<id>
    if (host.endsWith("youtube.com")) {
      const v = u.searchParams.get("v");
      if (v) return v;

      // youtube.com/shorts/<id> or /embed/<id>
      const parts = u.pathname.split("/").filter(Boolean);
      const idx = parts.findIndex((p) => p === "shorts" || p === "embed");
      if (idx >= 0 && parts[idx + 1]) return parts[idx + 1];
    }
  } catch {
    // ignore invalid URLs
  }
  return null;
}

export function CoursePlayer() {
  const { courseId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const resumeInitializedRef = useRef(false);
  const lastSyncedSecondsRef = useRef(0);
  const lastHeartbeatRef = useRef(0);
  const playerRef = useRef(null);
  const syncProgressRef = useRef(null);
  const latestTimeRef = useRef({ current: null, duration: null });

  useEffect(() => {
    lastSyncedSecondsRef.current = 0;
    resumeInitializedRef.current = false;
    let cancelled = false;
    (async () => {
      try {
        const d = await api(`/api/learnflow/courses/${courseId}`);
        if (!cancelled) {
          setData(d);
          lastSyncedSecondsRef.current = Math.max(0, Number(d?.resume_seconds || 0));
          resumeInitializedRef.current = true;
        }
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Failed to load course");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [courseId]);

  const ytId = useMemo(() => extractYouTubeId(data?.youtube_url), [data?.youtube_url]);

  useEffect(() => {
    if (!ytId || !resumeInitializedRef.current) return;

    const resumeSeconds = Math.max(0, Number(data?.resume_seconds || 0));

    const initPlayer = () => {
      if (!window.YT || !window.YT.Player) {
        setTimeout(initPlayer, 100);
        return;
      }
      
      if (playerRef.current) {
        try {
          if (playerRef.current.getVideoData && playerRef.current.getVideoData().video_id !== ytId) {
            playerRef.current.loadVideoById({videoId: ytId, startSeconds: resumeSeconds});
          }
        } catch(e) {}
        return;
      }

      playerRef.current = new window.YT.Player("yt-player", {
        videoId: ytId,
        host: 'https://www.youtube-nocookie.com',
        playerVars: {
          autoplay: 0,
          rel: 0,
          controls: 1,
          playsinline: 1,
          modestbranding: 1,
          iv_load_policy: 3,
          start: resumeSeconds,
          origin: window.location.origin,
        },
        events: {
          onStateChange: (event) => {
            if (event.data === window.YT.PlayerState.ENDED) {
              if (syncProgressRef.current) {
                syncProgressRef.current(true, true);
              }
            }
          }
        }
      });
    };

    if (!window.YT) {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      const firstScriptTag = document.getElementsByTagName("script")[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
      window.onYouTubeIframeAPIReady = initPlayer;
    } else {
      initPlayer();
    }
  }, [ytId, resumeInitializedRef.current]);

  useEffect(() => {
    if (!courseId || !ytId || !resumeInitializedRef.current) return undefined;
    if (location.pathname !== `/courses/${courseId}`) return undefined;
    const heartbeatSeconds = 10;
    let timerId = 0;

    const syncProgress = async (force = false, isEnded = false) => {
      if (!force && (document.hidden || !document.hasFocus() || location.pathname !== `/courses/${courseId}`)) {
        return;
      }
      
      let currentSeconds = latestTimeRef.current.current;
      let durationSeconds = latestTimeRef.current.duration;
      let isPlaying = false;

      if (playerRef.current && playerRef.current.getCurrentTime) {
        try {
            const state = playerRef.current.getPlayerState();
            const dur = Math.floor(playerRef.current.getDuration());
            if (dur > 0) durationSeconds = dur;
            
            if ((state === 0 || isEnded) && durationSeconds > 0) {
                // If video ended, force currentSeconds to duration
                currentSeconds = durationSeconds;
            } else {
                const ct = Math.floor(playerRef.current.getCurrentTime());
                if (ct >= 0) currentSeconds = ct;
            }
            isPlaying = (state === 1); // 1 = playing
            
            // Update cache
            latestTimeRef.current.current = currentSeconds;
            latestTimeRef.current.duration = durationSeconds;
        } catch(e) {}
      }

      const now = Date.now();
      const elapsedSeconds = Math.max(0, Math.floor((now - lastHeartbeatRef.current) / 1000));
      // Only record watched seconds if the video was actually playing
      const secondsWatched = (isPlaying || force) ? Math.min(elapsedSeconds, heartbeatSeconds) : 0;
      
      // If we aren't playing and have nothing to update, skip the API call
      if (!force && secondsWatched <= 0 && currentSeconds === lastSyncedSecondsRef.current) return;
      
      lastHeartbeatRef.current = now;

      try {
        const res = await api(`/api/learnflow/courses/${courseId}/watch-progress`, {
          method: "POST",
          body: JSON.stringify({
            seconds_watched: secondsWatched,
            current_seconds: currentSeconds,
            duration_seconds: durationSeconds,
          }),
        });
        lastSyncedSecondsRef.current = Math.max(0, Number(res.resume_seconds || currentSeconds || lastSyncedSecondsRef.current));
        setData((prev) =>
          prev
            ? {
                ...prev,
                progress_percent: res.progress_percent,
                status: res.status,
                resume_seconds: res.resume_seconds,
              }
            : prev,
        );
      } catch {
        // retry on next tick
      }
    };

    lastHeartbeatRef.current = Date.now();
    syncProgressRef.current = syncProgress;
    timerId = window.setInterval(() => syncProgress(false), heartbeatSeconds * 1000);

    return () => {
      if (timerId) window.clearInterval(timerId);
      void syncProgress(true);
    };
  }, [courseId, ytId, location.pathname]);

  if (err) {
    return (
      <div className="p-8">
        <p className="text-red-600">{err}</p>
        <div className="mt-4">
          <button onClick={() => navigate(-1)} className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:underline">
            <ArrowLeft className="h-4 w-4" />
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return <div className="flex min-h-[50vh] items-center justify-center text-slate-500">Loading course…</div>;
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] p-6 lg:p-10">
      <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <button onClick={() => navigate(-1)} className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors focus:outline-none">
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <h1 className="mt-3 truncate font-display text-3xl text-slate-900">{data.title}</h1>
          <p className="mt-1 text-sm text-slate-500">{data.author} · {data.category}</p>
        </div>

        {data.youtube_url ? (
          <a
            href={data.youtube_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm ring-1 ring-slate-200 hover:bg-slate-50"
          >
            <ExternalLink className="h-4 w-4" />
            Open on YouTube
          </a>
        ) : null}
      </header>

      <div className="grid gap-6 lg:grid-cols-[1.7fr_1fr]">
        <section className="rounded-2xl border border-slate-100 bg-white shadow-sm">
          {ytId ? (
            <div className="aspect-video w-full bg-black">
              <div id="yt-player" className="h-full w-full"></div>
            </div>
          ) : (
            <div className="flex min-h-[360px] flex-col items-center justify-center gap-3 p-8 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-50 text-slate-600">
                <Play className="h-6 w-6" />
              </div>
              <h2 className="font-display text-xl text-slate-900">No YouTube link set</h2>
              <p className="max-w-md text-sm text-slate-500">
                Is course ke liye abhi YouTube URL add nahi hai. Enroll time pe link daloge to yaha video auto-open ho jayega.
              </p>
            </div>
          )}
        </section>

        <aside className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <h2 className="font-display text-lg text-slate-900">Course Details</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex items-center justify-between gap-4">
              <dt className="text-slate-500">Progress</dt>
              <dd className="font-semibold text-slate-900">{data.progress_percent}%</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="text-slate-500">Status</dt>
              <dd className="font-semibold text-slate-900">{data.status}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="text-slate-500">Resume From</dt>
              <dd className="font-semibold text-slate-900">
                {Math.floor((data.resume_seconds || 0) / 60)}m {(data.resume_seconds || 0) % 60}s
              </dd>
            </div>
          </dl>

          {data.youtube_url ? (
            <div className="mt-6 rounded-xl bg-slate-50 p-4 text-xs text-slate-600 break-all">
              <div className="font-semibold text-slate-700">YouTube URL</div>
              <div className="mt-1">{data.youtube_url}</div>
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}

