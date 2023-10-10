import React from "react";
import ReactDOM from "react-dom";
import { IntegrationTestsForm } from "./IntegrationTestsForm";
import { OverridableContext, overrideStore } from "react-overridable";

const overriddenComponents = overrideStore.getAll();

ReactDOM.render(
  <OverridableContext.Provider value={overriddenComponents}>
    <IntegrationTestsForm />
  </OverridableContext.Provider>,
  document.getElementById("integration-tests-form")
);
