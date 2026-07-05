# Optional: Exploring the CircleCI config file

This step-by-step tutorial shows you  how to create a full CI/CD pipeline in CircleCI. However, before you start building this pipeline, you need to run the following setup:


```python
import warnings
warnings.filterwarnings('ignore')
```

## Load API tokens for our 3rd party APIs.


```python
from utils import get_circle_api_key
cci_api_key = get_circle_api_key()
```


```python
from utils import get_gh_api_key
gh_api_key = get_gh_api_key()
```


```python
from utils import get_openai_api_key
openai_api_key = get_openai_api_key()
```

### Set up our github branch


```python
from utils import get_repo_name
course_repo = get_repo_name()
course_repo
```


```python
from utils import get_branch
course_branch = get_branch()
course_branch
```

## Basic CircleCI configuration structure

CircleCI uses configuration as code, so everything your pipeline does is stored in a [CircleCI configuration file](https://circleci.com/docs/config-intro/).

All CI/CD pipelines in CircleCI are defined in a single YAML file at the path `.circleci/config.yml` in your project's Git repository. This tutorial explains the example configuration file used throughout the course.

There are three key components to every CircleCI config file: **jobs**, **commands**, and **workflows**.

### Jobs

A [job](https://circleci.com/docs/jobs-steps/) is the basic unit of automation in a CircleCI CI/CD pipeline. Each job represents one of the  high-level tasks you want to automate, containing the commands you want to execute to complete the task.

Each job  is defined in its own configuration section. The example snippet below defines a job, including the [Docker image](https://circleci.com/docs/using-docker/) that will be used to execute this job. When CircleCI executes this job, a cloud execution environment is created on CircleCI’s infrastructure, running the specified Docker image.

Any commands defined in the job will be run in this environment (including bash commands, Python scripts, and any other command or application executed inside the job). There are many other execution environments — we’ll explore these later in this lesson.

Here is an example job named `run-hello-world` that spins up an execution environment based on the `cimg/python` Docker image and then prints “Hello World!” to the console. 


```python
!cat hello_world.yml
```

Below, we have an entire config file that runs this job. This file uses other CircleCI configuration options that will be discussed later. For now, you can just focus on the `jobs` section at the bottom of this file.


```python
!cat circle_config_v1.yml
```

You can trigger this job by interacting with the [CircleCI API](https://circleci.com/docs/api-intro/). This is done by calling the helper functions below defined in `utils.py`. After the workflow begins running successfully, a link will be provided to view the results. Note that it may take a few seconds for the APIs to finish executing.


```python
print(course_repo)
print(course_branch)
```


```python
from utils import push_files
push_files(course_repo, 
           course_branch, 
           ["app.py", "test_assistant.py"],
           "circle_config_v1.yml"
          )
```


```python
from utils import trigger_commit_evals
trigger_commit_evals(course_repo, 
                     course_branch, 
                     cci_api_key)
```

### Commands

[Commands](https://circleci.com/docs/configuration-reference/#commands) are the individual steps executed in sequence inside of jobs. Commands can either be defined inline with the `run` keyword as we have done above, or created and named outside of jobs so that they can be used in multiple jobs. This second method of defining commands mimics the principle of DRY (don't repeat yourself) development, in which we create functions once and use them over and over.

When using the `run` keyword to define inline commands, the `name` field determines what you will see to identify the command in the CircleCI dashboard and the `command` field determines which command will be executed on the command line of the executor.

The example code below reworks the "Hello World" job to run the first type of eval that was covered in Lesson 2. Some additional required steps have been added as well: the [checkout](https://circleci.com/docs/configuration-reference/#checkout) step is a built-in CircleCI command that checks out the code from the repository containing the config file, while the `python/install-packages` step installs any Python packages included in `requirements.txt`.

The `python/install-packages` step is defined in the [Python orb](https://circleci.com/developer/orbs/orb/circleci/python) image we are using in this configuration. We'll go into more depth on orbs at the end of the tutorial.



```python
!cat circle_config_v2.yml
```

As you can see, this is running a Python unit test file `test_assistant.py` through Pytest instead of just echoing "Hello World". You can use the same `app.py` and `test_assistant.py` files that you used in the first lesson.

As in the previous example, this job can be triggered by interacting with the CircleCI API.


```python
from utils import push_files
push_files(course_repo, 
           course_branch, 
           ["app.py", "test_assistant.py"],
           "circle_config_v2.yml"
          )
```


```python
from utils import trigger_commit_evals
trigger_commit_evals(course_repo, course_branch, cci_api_key)
```

### Workflows

To run multiple types of evals, you need to define multiple jobs in your config file. You can use workflows in CircleCI to orchestrate these.

Put simply, a [workflow](https://circleci.com/docs/workflows/#overview) is used to orchestrate jobs. You can define multiple workflows that will run when you push to specific branches in your repository or run them on a schedule.  Workflows log their output to the [CircleCI dashboard](https://circleci.com/docs/introduction-to-the-circleci-web-app/), stopping when a job fails so that the output can be inspected.

Here's how you can add jobs for the other eval types into your workflow. Now, when the `evaluate-app` workflow is triggered, the `run-commit-evals` job **and** the new `run-pre-release-evals` job will be run. **Any number of jobs, containing any number of commands, can be defined and added to this workflow.**


```python
!cat circle_config_v3.yml
```

You can trigger the workflow again with the code below. By default the two jobs will run in parallel. Later we will show how you can adjust the workflow to make the jobs run in series or based on certain conditions.

**We have intentionally inserted a bug into `test_release_evals.py` so you can see what the output looks like when one of your tests fails.** You can see the output from the error by clicking on the failed job and scrolling down to the step that generated the error.


```python
from utils import push_files
push_files(course_repo, 
           course_branch, 
           ["app.py", "test_assistant.py", "test_release_evals.py"],
           config="circle_config_v3.yml"
          )
```


```python
from utils import trigger_commit_evals
trigger_commit_evals(course_repo, 
                     course_branch, 
                     cci_api_key)
```

## Enhancing your CircleCI configuration file

Jobs, commands, and workflows are key components of every CircleCI pipeline. However, there are many additional features within CircleCI that you can take advantage of to better orchestrate the flow of jobs.

### Conditional workflows

You can also execute different workflows on different conditions with [conditional workflows](https://circleci.com/docs/pipeline-variables/#conditional-workflows). Conditional workflows allow you to use if-statement logic in your CircleCI configuration.

For example, you might want to run the pre-commit evals whenever there is a push to your dev branches and the pre-release evals when there is a push to your main branch. In this configuration, we’ll show you how to conditionally execute different workflows by passing in [pipeline parameters](https://circleci.com/docs/pipeline-variables/#pipeline-parameters-in-configuration) to our workflows. However, you could also execute different workflows based on [pipeline values](https://circleci.com/docs/pipeline-variables/#pipeline-values) like `pipeline.git.branch`.

With pipeline parameters, you can define parameters for your configuration and change them in your application through [CircleCI’s API](https://circleci.com/docs/pipeline-variables/#passing-parameters-when-triggering-pipelines-via-the-api). The `utils.py` file in this example is used to pass in different `eval-mode` parameters based on this.

The CircleCI configuration snippet below runs different workflows based on the current `eval-mode`.


```python
!cat circle_config_v4.yml
```

This conditional workflow can be triggered with the commands below. We expect the `commit-workflow` to pass.


```python
from utils import push_files
push_files(course_repo, 
           course_branch, 
           ["app.py", "test_assistant.py", "test_release_evals.py"],
           config="circle_config_v4.yml"
          )
```


```python
from utils import trigger_commit_evals
trigger_commit_evals(course_repo, 
                     course_branch, 
                     cci_api_key)
```

For this optional lesson, we have implemented placeholder commands for pre-release and manual evals. We are including them to show an example of how to trigger different conditional behavior in workflows using the API.

To learn how to implement model graded evals and run them directly as part of the CI pipeline, please visit lesson 3 of this course. 


```python
from utils import trigger_release_evals
trigger_release_evals(course_repo, 
                      course_branch, 
                      cci_api_key)
```


```python
from utils import trigger_full_evals
trigger_full_evals(course_repo, 
                   course_branch, 
                   cci_api_key)
```

### Scheduled workflows

So far, all of these workflows have been triggered whenever a commit is made to a Git repository, which is typical for continuous integration. However, you might want to schedule your more comprehensive evals to run on a regular schedule for continuous delivery or deployment. This can be done with [scheduled workflows](https://circleci.com/docs/workflows/#scheduling-a-workflow).

For example, you could set up a nightly trigger to run a certain workflow by providing a standard `cron` syntax:


```python
!cat circle_config_v5.yml
```

## Some other features we've used

Throughout this tutorial, we have used other features of CircleCI as well, although we didn't focus on them as much. Despite this, each of the following features are key to building a functional CI/CD pipeline.

### Execution environments

CircleCI provides many different options for [execution environments](https://circleci.com/docs/executor-intro/), including Docker images, Linux VMs, MacOS VMs, Windows VMs, GPU executors, and even [self-hosted runners](https://circleci.com/docs/runner-overview/) to run jobs on your own infrastructure.

You can also run different jobs in the same workflow **on different machines**. Some example use cases for this would be using more expensive and specialized cloud-based GPU executors to train ML models or deploying applications to your own infrastructure after testing them on cloud infrastructure.

### Orbs

[Orbs](https://circleci.com/developer/orbs) are shareable packages of CircleCI configurations, similar to libraries or packages in conventional software development. CircleCI supports certified orbs, community orbs, and private orbs to bring the same advantages of libraries for product development to configuration development.

### Contexts

Security is paramount for any application. You shouldn't include credentials and other sensitive information (known as secrets) in your CircleCI configuration file, as it will be committed to your code repositories where it can potentially be exposed.

[Contexts](https://circleci.com/docs/contexts/#create-and-use-a-context) allow you to securely store certain credentials in one centralized location on CircleCI's infrastructure for access during certain workflows.

For this tutorial, you can see that we've been using the `dl-ai-courses` context, which contains various API keys for LangSmith, OpenAI, and other tools required for this tutorial.

## Building out your AI application and workflows

We've covered the major features of CircleCI that you can use to build this pipeline and similar ones as well. However, we've only scratched the surface. You can check out [CircleCI's documentation](https://circleci.com/docs/configuration-reference/) to see more advanced features and use cases.



```python

```
