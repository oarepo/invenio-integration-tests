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
      - name: Set up Python 3.8
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Generate OARepo setup.py from tested requirements artifact
        run: |
          ./scripts/generate_setup.sh invenioX.Y
          echo "NEWTAG=$(cat ./oarepo/oarepo/tag.txt)" >> $GITHUB_ENV
      - name: Commit and Push generated OARepo setup.py
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "[p2oarepo] update setup.py from oarepo/invenio-integration-tests (tag ${{ env.NEWTAG }})"
          branch: invenio-X.Y
          file_pattern: setup.py oarepo/version.py
          repository: oarepo
          commit_user_name: p2oarepo-workflow
          commit_user_email: p2oarepo-workflow@oarepo.org
          tagging_message: ${{ env.NEWTAG }}
          # Optional options appended to `git-push`
          push_options: '--force'
        if: success() && github.event_name == 'push'
