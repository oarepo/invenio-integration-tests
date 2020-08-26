  publish-setup-invenio-X-Y:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout oarepo/invenio-integration-tests
        uses: actions/checkout@v2
      - name: Checkout oarepo/oarepo under ./oarepo
        uses: actions/checkout@v2
        with:
          repository: 'oarepo/oarepo'
          ref: 'invenio-X.Y'
          token: '${{ secrets.OAR_BOT }}'
          path: 'oarepo'
      - name: Generate OARepo setup.py from tested requirements artifact
        run: |
          ./scripts/generate_setup.sh invenioX.Y
      - name: Commit and Push generated OARepo setup.py
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: '[p2oarepo] update setup.py from oarepo/invenio-integration-tests:actions-tests'
          branch: invenio-X.Y
          file_pattern: setup.py
          repository: oarepo
          commit_user_name: p2oarepo-workflow
          commit_user_email: p2oarepo-workflow@oarepo.org
          # TODO: tag the commit in format X.Y.Z.20200818 where first 3 digits are concrete invenio version
          # Optional options appended to `git-push`
          push_options: '--force'
        if: success() && github.event_name == 'push'
