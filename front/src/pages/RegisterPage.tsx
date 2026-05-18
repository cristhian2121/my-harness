import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { registerUser } from "@/api/client";
import { useUser } from "@/context/UserContext";

type RegisterFormValues = {
  username: string;
  role: string;
};

export default function RegisterPage() {
  const navigate = useNavigate();
  const { setCurrentUser } = useUser();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    defaultValues: {
      username: "",
      role: "viewer",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      setErrorMessage(null);
      const user = await registerUser(values);
      setCurrentUser(user);
      navigate("/chat");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "No se pudo registrar el usuario.";
      setErrorMessage(message);
    }
  });

  return (
    <section className="register-grid">
      <div className="intro-copy">
        <span className="eyebrow">Registro</span>
        <h1>Inicializa un usuario para operar el chat.</h1>
        <p>
          Esta vista crea el usuario en SQLite y deja listo el consumo de la API desde
          la vista de conversación.
        </p>
      </div>

      <form className="surface-panel form-panel" onSubmit={onSubmit}>
        <div className="field-group">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            className="text-field"
            placeholder="ana"
            {...register("username", {
              required: "Username is required.",
              minLength: { value: 3, message: "Use at least 3 characters." },
            })}
          />
          {errors.username ? <span className="field-error">{errors.username.message}</span> : null}
        </div>

        <div className="field-group">
          <label htmlFor="role">Role</label>
          <input
            id="role"
            className="text-field"
            placeholder="viewer"
            {...register("role", {
              required: "Role is required.",
              minLength: { value: 2, message: "Use at least 2 characters." },
            })}
          />
          {errors.role ? <span className="field-error">{errors.role.message}</span> : null}
        </div>

        {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}

        <button type="submit" className="button button--primary" disabled={isSubmitting}>
          {isSubmitting ? "Creating..." : "Create user"}
        </button>
      </form>
    </section>
  );
}
