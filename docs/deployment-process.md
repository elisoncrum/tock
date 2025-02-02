## Deploying to Cloud Foundry

[:arrow_left: Back to Tock Documentation](../docs)

**This section is only of interest to 18F team members.**

Download the Cloud Foundry CLI according to the [cloud.gov instructions][].

[cloud.gov instructions]: https://docs.cloud.gov/getting-started/setup/

We use the V7 Cloud Foundry CLI. If you're upgrading from V6, checkout [the CLI docs for instructions](https://github.com/cloudfoundry/cli).

Tock will be deployed to the GovCloud instance of cloud.gov:

```shell
# Login to cloud.gov
cf login -a api.fr.cloud.gov --sso
```

After authenticating, you'll need to target the org and space you want to work with. For example, if you wanted to work with the dev space:

```
cf target -o gsa-18f-tock -s dev
```

Manifest files, which contain import deploy configuration settings, are located
in the root directory of this project, prefixed with `manifest-` and ending in a
`.yml` file extension.

During local development and continuous integration testing,
`pipenv install --dev` is used. This installs both development
and production dependencies. During deployments, the `requirements.txt` file is used to install dependencies.

### Cloud Foundry structure

- cloud.gov environment: `GovCloud`
- Organization: `gsa-18f-tock`
- Spaces: `staging`, `prod`
- Apps:
  - `staging` space:
    - `tock-staging`
  - `prod` space:
    - `tock`
- Routes:
  - tock.app.cloud.gov -> `staging` space, `tock-staging` app
  - tock.18f.gov -> `prod` space, `tock` app

#### Cloud Foundry environment variables

In production, Tock requires a few different environment variables. These are
updated using the [User Provided Service](#user-provided-service) and
configured in the `manifest-*.yaml`.

| type | name | description |
| ---- | -----| ----------- |
| **secret** | `DJANGO_SECRET_KEY` | The secret key used to maintain session state. Changing this value will invalidate all user sessions for Tock and log out all users.|
| **secret** | `NEW_RELIC_LICENSE_KEY` | The New Relic license key connected to the New Relic account for the application. |
| **secret** | `NEW_RELIC_API_KEY` | The New Relic API key connected to the New Relic account for the application. |
| **secret** | `UAA_CLIENT_ID` | The UAA Client ID from the cloud.gov identity provider service key. |
| **secret** | `UAA_CLIENT_SECRET` | The UAA Client Secret from the cloud.gov identity provider service key. |
| **public** | `NEW_RELIC_CONFIG_FILE` | The New Relic configuration file used by the `newrelic-admin` commands and New Relic libraries. |
| **public** | `NEW_RELIC_APP_NAME` | The application name that appears in the New Relic interface. Changing this will change will cause New Relic data to be gathered under a different application name. |
| **public** | `NEW_RELIC_ENV` | The application environment that appears in the New Relic interface. |
| **public** | `NEW_RELIC_LOG` | Logging that New Relic should listen to: e.g. `stdout`. |

Variables with the designation **secret** are stored in the `tock-credentials`.
User-Provided Service (UPS). **Public** variables are stored in the
environment's `manifest-*.yml` file.

### Services

#### User-provided service (UPS)

For cloud.gov deployments, this project makes use of a [user-provided service (UPS)][UPS] to get its configuration
variables, instead of using the local environment (except for [New Relic-related environment variables](#new-relic-environment-variables)).

You will need to create a UPS called `tock-credentials`, provide 'credentials' to it, and link it to the
application instance. Please note that you'll need to do this for every Cloud Foundry `space`.

Once you've completed those steps, enter the following commands (filling in the main application instance name
for `<APP_INSTANCE>`) to create the user-provided service:

```sh
# Creating and uploading the credentials to the service
cf cups tock-credentials -p credentials-<ENVIRONMENT>.json

# Binding the service to the app
cf bind-service <APP_INSTANCE> tock-credentials

# Restaging the app to make use of the updated credentials.
cf restage <APP_INSTANCE> --strategy rolling
```

You can update the user-provided service with the following commands:

```sh
# Uploading the new credentials to the service
cf uups tock-credentials -p credentials-staging.json

# Restaging the app to make use of the updated credentials.
cf restage <APP_INSTANCE> --strategy rolling
```

#### Database service

Tock uses PostgreSQL for its database.

```sh
cf create-service aws-rds shared-psql tock-database
cf bind-service <APP_INSTANCE> tock-database
```

#### cloud.gov identity provider service

Tock uses the cloud.gov identity provider service to provide authentication via the
cloud.gov UAA application for its users.


#### cloud.gov service account

Tock uses the cloud.gov service account service to provide deployer accounts for
staging and production environments.

### Code review

Submissions to the Tock codebase are made via GitHub, and are only accepted into the main
branch after review. At least one approving review is required before a branch is merged
to main, and this restriction is enforced by Tock's GitHub settings.
Your reviewer will usually merge the branch for you.

Code review covers both code (such as Python or JavaScript) and configuration (such as
Dockerfiles, CloudFoundry manifest files, etc.).

Code reviews should be conducted [following the 18F Engineering Guide](https://engineering.18f.gov/code-review/) and include an assessment of:

- Simplicity. Ideally the submission implements the feature/fix with as little complexity as possible.
- Legibility. Ideally the submission is easy to understand.
- Security. The submission is reviewed for security considerations.

Code review is in addition to the various automated checks, which include tests, linting,
and checks on security flaws of Tock's dependencies.

### CircleCI continuous integration, delivery, and deployment

Tock uses CircleCI to continuously integrate code, deliver the code to staging
servers, and deploy the latest release to production servers.

### New Relic environment variables

Basic New Relic configuration is done in [newrelic.ini](../newrelic.ini), with
additional settings specified in each deployment environment's manifest file.

As described in [Environment variables](#cloud-foundry-environment-variables), you will need
to supply the `NEW_RELIC_LICENSE_KEY` as part of each deployment's
[user-provided service](#user-provided-service-ups).

### Staging server

The staging server updates automatically when changes are merged into the
`main` branch. Check out the `workflows` sections of
the [CircleCI config](../.circleci/config.yml) for details and settings.

Should you need to, you can push directly to tock.app.cloud.gov with the following:

```sh
cf target -o gsa-18f-tock -s staging
cf push tock-staging -f manifest-staging.yml --strategy rolling
```

### Production servers

Production deploys are also automated. They rely on the creation of a Git tag to
be made against the `main` branch following the [_Automated Releases to
Production_](#automated-releases-to-production) workflow.

In some cases, you may need to make a manual deployment to production. If this is the case, please make
sure you're using the rolling deployment strategy with `--strategy rolling`

To deploy, first make sure you're targeting the prod space:

```sh
cf target -o gsa-18f-tock -s prod
```

Create a `VERSION` file with the name of the version that is being deployed to
production either with the Git SHA1 for the latest commit or the Git tag for the
latest release:

```sh
# Manually creating a VERSION file from the latest Git SHA1 commit
echo $(git rev-parse HEAD | head -c 7) > tock/VERSION

# Manually creating a VERSION file from the latest Git Tag release
echo $(git describe --abbrev=0 --tags) > tock/VERSION
```

Then use the CLI to deploy:

```sh
cf push tock -f manifest-production.yml --strategy rolling
```

#### Troubleshooting failed deployments

If at any point the deployment fails, we can use the CLI to recover to our previous state.

https://docs.cloudfoundry.org/devguide/deploy-apps/rolling-deploy.html#cancel

```
cf cancel-deployment tock
```

### Logs

Logs in cloud.gov-deployed applications are generally viewable by running
`cf logs <APP_NAME> --recent`.

[UPS]: https://docs.cloudfoundry.org/devguide/services/user-provided.html
[`README.md`]: https://github.com/18F/tock#readme

## Releasing Tock

Releasing Tock onto Production happens whenever you create a Git tag and push it
up to the repository. The process is outlined in the `Creating a GitHub release` section.

You can manually create Git tags using the Git CLI as outlined in the next section. You can
also create them in the GitHub release interface when drafting and publishing
the release.

To create a new tag in the GitHub release interface (and skip the Git tag CLI step):

- Click the tag name dropdown located above the release title text input.
- Type the name of your new tag, be sure to follow the tag naming guidelines of using
a `v` followed by the full year, full month, and full day, followed by a period
and a version number for that release. For example: `v20211008.1`
- Click the "+ Create new tag: `v20211008.1` on publish" link that appears below your
newly named tag.

## Creating a GitHub release

<details>
<summary>GitHub Release Template</summary>

```markdown
### For Those About To Tock

#### Liner Notes, XX/XX/XXXX

<!-- Summary of changes -->
---

##### Stuff You Can See:

<!-- List items of changes with PR links -->
<!-
  - Example: - None. PR: [#1987](https://www.youtube.com/watch?v=dQw4w9WgXcQ&allow=autoplay)
-->
-

---

##### Admin-only Features:

<!-- List items of changes with PR links -->
<!-
  - Example: - None. PR: [#1987](https://www.youtube.com/watch?v=dQw4w9WgXcQ&allow=autoplay)
-->
-

---

##### Under The Hood:

<!-- List items of changes with PR links -->
<!-
  - Example: - None. PR: [#1987](https://www.youtube.com/watch?v=dQw4w9WgXcQ&allow=autoplay)
-->
-

---

##### Code Contributors for this release

Team Tock would like to thank:

<!-- List folks not on the Tock team who contributed commits / code -->
<!-
  - @username
-->
-
```

</details>

#### Automated releases to production

Tock is automatically deployed to Production using CircleCI, GitHub
releases, and Git tags. Tags are versioned using the following structure: the
letter `v` followed by the full year, full month, and full day, followed by a period
and a version number for that release. For example:

```sh
# Create the tag
git tag v20180131.1

# Push the tags up to GitHub
git push --tags
```

If you need to release multiple versions in a single day, increment the
number after the period (e.g., `v20180131.1` turns into `v20180131.2`).

Once you push this tag up to GitHub, draft or assign it to an already
drafted release in GitHub. CircleCI will deploy this tag to the Production
instance of Tock.


## Maintenance Mode
A simple static application exists to display a maintenance
page if/when Tock needs to be taken offline.

To show the maintenance page you will need to manually map Tock's production
route to this application.
```sh
cf target -o gsa-18f-tock -s prod
cf map-route tock-maintenance tock.18f.gov
```

Upon a new automatic release, the production route will be mapped back to the production app.

To manually re-map the route and exit "maintenance mode":
```sh
cf target -o gsa-18f-tock -s prod
cf map-route tock tock.18f.gov
```
To deploy this static application:

1. `cd` into ./tock/maintenance_page/
2. run `cf push`
