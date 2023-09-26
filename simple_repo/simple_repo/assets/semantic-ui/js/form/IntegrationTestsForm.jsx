import React from "react";
import PropTypes from "prop-types";
import { Container, Grid, Card } from "semantic-ui-react";
import { TextField, BaseForm } from "react-invenio-forms";
import Overridable from "react-overridable";
import { PublishButton } from "./PublishButton";
import { OARepoDepositApiClient, OARepoDepositSerializer } from "../api";

export const IntegrationTestsForm = () => {
  const createUrl = "/api/simple-records";
  const newItem = {};

  const recordSerializer = new OARepoDepositSerializer([], []);

  const apiClient = new OARepoDepositApiClient(createUrl, recordSerializer);

  return (
    <Container>
      <BaseForm
        onSubmit={() => {}}
        formik={{
          initialValues: newItem,
          validationSchema: undefined,
          validateOnChange: false,
          validateOnBlur: false,
          enableReinitialize: true,
        }}
      >
        <Grid>
          <Grid.Column mobile={16} tablet={16} computer={11}>
            <TextField fieldPath="title" label={"Title"} required />
          </Grid.Column>
          <Grid.Column mobile={16} tablet={16} computer={5}>
            <Overridable id="FormApp.buttons">
              <Card fluid>
                <Card.Content>
                  <Grid>
                    <Grid.Column width={16}>
                      <PublishButton apiClient={apiClient} />
                    </Grid.Column>
                  </Grid>
                </Card.Content>
              </Card>
            </Overridable>
          </Grid.Column>
        </Grid>
      </BaseForm>
    </Container>
  );
};
