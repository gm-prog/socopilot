import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import ValidationErrorBoundary from "./components/ValidationErrorBoundary";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ValidationErrorBoundary>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ValidationErrorBoundary>
  </React.StrictMode>
);
