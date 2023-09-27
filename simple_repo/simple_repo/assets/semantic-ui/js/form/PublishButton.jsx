import React from "react";
import { Button } from "semantic-ui-react";
import { i18next } from "@translations/invenio_app_rdm/i18next";
import { useFormikContext } from "formik";

export const PublishButton = ({ apiClient }) => {
  const { values } = useFormikContext();
  const handleCreate = () => {
    apiClient.createDraft(values).then((response) => {
      console.log(response);
      window.location.href = response.links.ui;
    });
  };
  return (
    <Button
      id="publish-button"
      fluid
      color="green"
      // onClick={() => {
      //   apiClient.createDraft(values);
      // }}
      onClick={handleCreate}
      icon="upload"
      labelPosition="left"
      content={i18next.t("publish")}
      type="button"
    />
  );
};
