import dotenv
dotenv.load_dotenv()

from crewai import Agent, Crew, Task
from crewai.project import CrewBase, agent, task, crew


@CrewBase
class TranslaterCrew:

    @agent
    def translator_agent(self):
        return Agent(
            config=self.agents_config["translator_agent"]
        )

    @task
    def translate_task(self):
        return Task(
            config=self.tasks_config["translator_task"]
        )

    @task
    def retranslate_task(self):
        return Task(
            config=self.tasks_config["retranslator_task"]
        )

    @crew
    def assemble_crew(self):
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True
        )

TranslaterCrew().assemble_crew().kickoff(inputs={"sentence": "Hello, how are you?"})