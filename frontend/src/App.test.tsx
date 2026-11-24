import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "./App";

describe("App", () => {
  it("renders the investigation shell", () => {
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText("ANVESHAK")).toBeInTheDocument();
    expect(screen.getByText("Investigation Dashboard")).toBeInTheDocument();
  });
});
