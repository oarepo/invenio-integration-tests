import { createSearchAppInit } from "@js/invenio_search_ui";
import { overrideStore } from "react-overridable";
import { ResultsListItem } from "./ResultsListItem";

const appName = "IntegrationTests.Search";
export const defaultComponents = {
  [`${appName}.ResultsList.item`]: ResultsListItem,
};
const overriddenComponents = overrideStore.getAll();
createSearchAppInit(
  { ...defaultComponents, ...overriddenComponents },
  true,
  "invenio-search-config",
  true
);
