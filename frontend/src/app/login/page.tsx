"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

const USERNAME = process.env.NEXT_PUBLIC_LOGIN_USER || "bridgewell";
const PASSWORD = process.env.NEXT_PUBLIC_LOGIN_PASS || "supersecret";

export default function LoginPage() {
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      localStorage.getItem("bridgewell-auth") === "1"
    ) {
      router.replace("/");
    }
  }, [router]);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (user === USERNAME && pass === PASSWORD) {
      localStorage.setItem("bridgewell-auth", "1");
      router.replace("/");
    } else {
      setError("Invalid credentials");
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f3f4f6",
      }}
    >
      <form
        onSubmit={handleLogin}
        style={{
          width: 340,
          background: "#fff",
          borderRadius: 12,
          boxShadow: "0 4px 24px rgba(0,0,0,0.07)",
          padding: 32,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <Image
          src="/logo.png"
          alt="Bridgewell Logo"
          width={80}
          height={80}
          style={{
            marginBottom: 16,
            objectFit: "contain",
          }}
        />
        <h2
          style={{
            marginBottom: 24,
            color: "#2563eb",
            fontWeight: 700,
            fontSize: 24,
          }}
        >
          Bridgewell Team Login
        </h2>
        <input
          type="text"
          placeholder="Username"
          value={user}
          onChange={(e) => setUser(e.target.value)}
          style={{
            width: "100%",
            marginBottom: 16,
            padding: 10,
            borderRadius: 6,
            border: "1px solid #e5e7eb",
            fontSize: 16,
          }}
        />
        <input
          type="password"
          placeholder="Password"
          value={pass}
          onChange={(e) => setPass(e.target.value)}
          style={{
            width: "100%",
            marginBottom: 16,
            padding: 10,
            borderRadius: 6,
            border: "1px solid #e5e7eb",
            fontSize: 16,
          }}
        />
        <button
          type="submit"
          style={{
            width: "100%",
            padding: 10,
            background: "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            fontWeight: 600,
            fontSize: 16,
            marginBottom: 8,
            cursor: "pointer",
          }}
        >
          Login
        </button>
        {error && (
          <div style={{ color: "#dc2626", marginTop: 4, fontSize: 14 }}>
            {error}
          </div>
        )}
      </form>
    </div>
  );
}
