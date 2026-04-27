import { AlertCircle, Loader2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";

export function AddTaskModal({ isOpen, onClose, onTaskAdded }) {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchingCourses, setFetchingCourses] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    course_id: "",
    title: "",
    description: "",
    deadline: "",
  });

  useEffect(() => {
    if (isOpen) {
      setFetchingCourses(true);
      api("/api/learnflow/courses?status=all")
        .then((data) => {
          setCourses(data.courses || []);
          if (data.courses?.length > 0) {
            setFormData((f) => ({ ...f, course_id: data.courses[0].id }));
          }
        })
        .catch((e) => setError("Failed to load courses. " + e.message))
        .finally(() => setFetchingCourses(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!formData.course_id) {
      setError("Please select a course to add a task.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        title: formData.title,
        description: formData.description,
        deadline: formData.deadline,
        status: "pending",
      };

      await api(`/api/tasks/course/${formData.course_id}`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      onTaskAdded(formData.deadline);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
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
      <div className="relative w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-slate-900/5 sm:rounded-3xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <h2 className="font-display text-xl text-slate-900">Add New Task</h2>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="max-h-[calc(100vh-8rem)] overflow-y-auto px-6 py-6">
          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-xl bg-red-50 p-4 text-sm text-red-800">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
              <p>{error}</p>
            </div>
          )}

          <form id="add-task-form" onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div>
              <label htmlFor="task-course-id" className="mb-1.5 block text-sm font-semibold text-slate-700">Course</label>
              <select
                id="task-course-id"
                name="course_id"
                required
                value={formData.course_id}
                onChange={handleChange}
                disabled={fetchingCourses}
                className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none ring-blue-500/20 focus:border-blue-500 focus:bg-white focus:ring-4 transition-all disabled:opacity-60"
              >
                {fetchingCourses ? (
                  <option>Loading courses...</option>
                ) : courses.length === 0 ? (
                  <option>No courses available</option>
                ) : (
                  courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title}
                    </option>
                  ))
                )}
              </select>
            </div>

            <div>
              <label htmlFor="task-title" className="mb-1.5 block text-sm font-semibold text-slate-700">Task Title</label>
              <input
                id="task-title"
                type="text"
                name="title"
                required
                placeholder="e.g. Complete chapter 5 exercises"
                value={formData.title}
                onChange={handleChange}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none ring-blue-500/20 focus:border-blue-500 focus:bg-white focus:ring-4 transition-all"
              />
            </div>

            <div>
              <label htmlFor="task-description" className="mb-1.5 block text-sm font-semibold text-slate-700">Description</label>
              <textarea
                id="task-description"
                name="description"
                rows="3"
                placeholder="Add necessary details or steps..."
                value={formData.description}
                onChange={handleChange}
                className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none ring-blue-500/20 focus:border-blue-500 focus:bg-white focus:ring-4 transition-all"
              />
            </div>

            <div>
              <label htmlFor="task-deadline" className="mb-1.5 block text-sm font-semibold text-slate-700">Deadline</label>
              <input
                id="task-deadline"
                type="date"
                name="deadline"
                required
                value={formData.deadline}
                onChange={handleChange}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 outline-none ring-blue-500/20 focus:border-blue-500 focus:bg-white focus:ring-4 transition-all"
              />
            </div>
          </form>
        </div>

        <div className="border-t border-slate-100 bg-slate-50 px-6 py-4 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-200 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            form="add-task-form"
            disabled={loading || fetchingCourses}
            className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition-all disabled:opacity-50"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Save Task
          </button>
        </div>
      </div>
    </div>
  );
}
