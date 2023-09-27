import React from "react";
import { Item } from "semantic-ui-react";

export const ResultsListItem = ({ result }) => {
  return (
    <Item href={result.links.ui} id="record">
      <Item.Content>
        <Item.Header>{result.title}</Item.Header>
      </Item.Content>
    </Item>
  );
};
