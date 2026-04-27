import { AlertCircle, Loader2, X } from "lucide-react";
import { useState } from "react";
import { api } from "../api/client";

export function EnrollCourseModal({ isOpen, onClose, onCourseEnrolled }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    title: "",
    category: "Programming",
    author: "",
    youtube_url: "",
  });

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    const youtubeUrl = formData.youtube_url.trim();
    if (!youtubeUrl) {
      setError("YouTube URL is required.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        title: formData.title,
        category: formData.category,
        author: formData.author || "Self Paced",
        youtube_url: youtubeUrl,
      };

      await api(`/api/learnflow/courses`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      onCourseEnrolled();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to enroll course");
    } finally {
      setLoading(false);
    }
  }

  function handleChange(e) {
    setFormData((f) => ({ ...f, [e.target.name]: e.target.value }));
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-center bg-slate-900/40 p-4 pt-10 backdrop-blur-sm sm:items-center sm:p-0">
      <div 
        className="fixed inset-0"
        onClick={onClose}
      />
      <div className="relative w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-slate-900/5 sm:rounded-3xl animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4 bg-white/50 backdrop-blur-md">
          <h2 className="font-display text-xl text-slate-900 font-semibold">Join New Course</h2>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-xl bg-red-50 p-4 text-sm text-red-800">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
              <p>{error}</p>
            </div>
          )}

          <p className="mb-6 text-sm text-slate-600">
            Provide the basic course details below to add it to your learning catalog.
          </p>

          <form id="enroll-course-form" onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div>
              <label htmlFor="enroll-title" className="mb-1.5 block text-sm font-semibold text-slate-700">Course Title <span className="text-red-500">*</span></label>
              <input
                id="enroll-title"
                type="text"
                name="title"
                required
                placeholder="e.g. Master Next.js App Router"
                value={formData.title}
                onChange={handleChange}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none ring-blue-500/20 focus:border-blue-500 focus:bg-white focus:ring-4 transition-all"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label htmlFor="enroll-category" className="mb-1.5 block text-sm font-semibold text-slate-700">Category <span className="text-red-500">*</span></label>
                <div className="relative">
                  <select
                    id="enroll-category"
                    name="category"
                    required
                    value={formData.category}
                    onChange={handleChange}
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none ring-blue-500/20 focus:border-blue-500 focus:bg-white focus:ring-4 transition-all"
                  >
                    <option value="Programming">Programming</option>
                    <option value="Design">Design / UI</option>
                    <option value="Business">Business</option>
                    <option value="Mathematics">Mathematics</option>
                    <option value="Data Science">Data Science</option>
                    <option value="General">General / Other</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400">
                    <svg className="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                      <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                    </svg>
                  </div>
                </div>
              </div>

              <div>
                <label htmlFor="enroll-author" className="mb-1.5 block text-sm font-semibold text-slate-700">Instructor Name</label>
                <input
                  id="enroll-author"
                  type="text"
                  name="author"
                  placeholder="e.g. FreeCodeCamp"
                  value={formData.author}
                  onChange={handleChange}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none ring-blue-500/20 focus:border-blue-500 focus:bg-white focus:ring-4 transition-all"
                />
              </div>
            </div>

            <div>
              <label htmlFor="enroll-youtube-url" className="mb-1.5 block text-sm font-semibold text-slate-700">YouTube Video Link <span className="text-red-500">*</span></label>
              <input
                id="enroll-youtube-url"
                type="url"
                name="youtube_url"
                required
                placeholder="e.g. https://www.youtube.com/watch?v=..."
                value={formData.youtube_url}
                onChange={handleChange}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none ring-blue-500/20 focus:border-blue-500 focus:bg-white focus:ring-4 transition-all"
              />
              <p className="mt-1.5 text-xs text-slate-500">
                Required. Add a YouTube link so the course opens directly to the video.
              </p>
            </div>
          </form>
        </div>

        <div className="border-t border-slate-100 bg-slate-50/80 px-6 py-4 flex justify-end gap-3 backdrop-blur-sm">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-200 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="enroll-course-form"
            disabled={loading}
            className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition-all disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Confirm Enrollment
          </button>
        </div>
      </div>
    </div>
  );
}
