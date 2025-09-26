from typing import Literal, List

from crewai import Agent, LLM
from crewai.flow.flow import Flow, listen, start, router, or_
from pydantic import BaseModel

from tools import web_search_tool
from seo_crew import SeoCrew
from virality_crew import ViralityCrew


class BlogPost(BaseModel):
    title: str
    subtitle: str
    sections: List[str]


class Tweet(BaseModel):
    content: str
    hashtags: str


class LinkedInPost(BaseModel):
    hook: str
    content: str
    call_to_action: str


class Score(BaseModel):
    score: int = 0
    reason: str = ""


class ContentPipelineState(BaseModel):
    # Inputs
    content_type: str = ""
    topic: str = ""
    # Internal
    max_length: int = 0  # 본문 길이
    score: Score | None = None  # 완성도 점수
    research: str = ""

    # Content
    blog_post: BlogPost | None = None
    tweet: Tweet | None = None
    linkedin_post: LinkedInPost | None = None


class ContentPipelineFlow(Flow[ContentPipelineState]):

    @start()
    def init_content_pipeline(self):
        content_type = self.state.content_type
        if content_type not in ["tweet", "blog", "linkedin"]:
            raise ValueError(f"Unknown content type: {content_type}. Allowed: tweet, blog, linkedin")
        if self.state.topic == "":
            raise ValueError("Empty topic")
        self.assign_max_length(content_type)

    @listen(init_content_pipeline)
    def conduct_research(self):
        print("Researching....")
        researcher = Agent(
            role="Head Researcher",
            goal=f"주어진 {self.state.topic} 주제에 관련해서 흥미롭고 유용한 것 정보들을 찾아 내세요.",
            backstory="당신은 흥미로운 사실과 통찰력을 파헤치는 것을 좋아하는 디지털 탐정과 같습니다. 당신은 다른 사람들이 놓치는 좋은 것들을 찾는 재주가 있습니다.",
            tools=[web_search_tool]
        )
        self.state.research = researcher.kickoff(f"주어진 {self.state.topic} 주제에 관련해서 흥미롭고 유용한 것 정보들을 찾아 내세요.")

    @router(conduct_research)
    def conduct_research_router(self):
        content_type = self.state.content_type
        if content_type == "blog":
            return "make_blog"
        elif content_type == "tweet":
            return "make_tweet"
        return "make_linkedin_post"

    @listen(or_("make_blog", "remake_blog"))
    def handle_make_blog(self):
        # if a blog post has been made, show the old one to the AI and ask it to improve, else
        # just ask to create.
        blog_post = self.state.blog_post
        llm = LLM(model="gpt-5-nano", response_format=BlogPost)

        if blog_post is None:
            result = llm.call(
                f"""
                Make a blog post with SEO practices on the topic {self.state.topic} using the following research: 
                Max length should be under {self.state.max_length}
                <research>
                ================
                {self.state.research}
                ================
                </research>
                """
            )
        else:
            result = llm.call(
                f"""
                You wrote this blog post on {self.state.topic}, but it does not have a good SEO score because of {self.state.score.reason} 
                Improve it.
                Max length of section's total content should be under {self.state.max_length}
                <blog post>
                {self.state.blog_post.model_dump_json()}
                </blog post>
                Use the following research.
                <research>
                ================
                {self.state.research}
                ================
                </research>
                """
            )
        self.state.blog_post = BlogPost.model_validate_json(result)  # bug 가 있어서 BlogPost object 로 못 받아온다.
        print("Making blog post...")

    @listen(or_("make_tweet", "remake_tweet"))
    def handle_make_tweet(self):
        # if a tweet has been made, show the old one to the AI and ask it to improve, else
        # just ask to create.
        tweet = self.state.tweet
        llm = LLM(model="openai/o4-mini", response_format=Tweet)
        if tweet is None:
            result = llm.call(
                f"""
                    Make a tweet that can go viral on the topic {self.state.topic} using the following research:
                    Max length of content should be under {self.state.max_length}
                    <research>
                    ================
                    {self.state.research}
                    ================
                    </research>
                    """
            )
        else:
            result = llm.call(
                f"""
                    You wrote this tweet on {self.state.topic}, but it does not have a good virality score because of {self.state.score.reason} 
                    Improve it.
                    Max length of content should be under {self.state.max_length}
                    <tweet>
                    {self.state.tweet.model_dump_json()}
                    </tweet>

                    Use the following research.
                    <research>
                    ================
                    {self.state.research}
                    ================
                    </research>
                    """
            )
        self.state.tweet = Tweet.model_validate_json(result)
        print("Making tweet...")

    @listen(or_("make_linkedin_post", "remake_linkedin_post"))
    def handle_make_linkedin_post(self):
        # if a post has been made, show the old one to the AI and ask it to improve, else
        # just ask to create.
        linkedin_post = self.state.linkedin_post
        llm = LLM(model="openai/o4-mini", response_format=LinkedInPost)

        if linkedin_post is None:
            result = llm.call(
                f"""
                    Make a linkedin post that can go viral on the topic {self.state.topic} using the following research:
                    Max length of content should be under {self.state.max_length}
                    <research>
                    ================
                    {self.state.research}
                    ================
                    </research>
                    """
            )
        else:
            result = llm.call(
                f"""
                    You wrote this linkedin post on {self.state.topic}, but it does not have a good virality score because of {self.state.score.reason} 
                    Improve it.
                    Max length of content should be under {self.state.max_length}
                    <linkedin_post>
                    {self.state.linkedin_post.model_dump_json()}
                    </linkedin_post>
                    Use the following research.
                    <research>
                    ================
                    {self.state.research}
                    ================
                    </research>
                    """
            )

        self.state.linkedin_post = LinkedInPost.model_validate_json(result)
        print("Making linkedin post...")

    @router(or_(handle_make_linkedin_post, handle_make_tweet, handle_make_blog))
    def score_router(self):
        content_type = self.state.content_type
        content_length: int = 0
        if content_type == "blog":
            for section in self.state.blog_post.sections:
                content_length += len(section)
            if content_length > self.state.max_length:
                return "remake_blog"
        elif content_type == "tweet":
            if content_length > len(self.state.tweet.content):
                return "remake_tweet"
        return "remake_linkedin_post"

    @listen(handle_make_blog)
    def check_seo(self):
        result = (SeoCrew().crew().kickoff(inputs={
            "topic": self.state.topic,
            "blog_post": self.state.blog_post.model_dump_json(),
        }))
        self.state.score = result.pydantic

    @listen(or_(handle_make_tweet, handle_make_linkedin_post))
    def check_virality(self):
        result = (
            ViralityCrew().crew().kickoff(inputs={
            "topic": self.state.topic,
            "content_type": self.state.content_type,
            "content": (
                self.state.tweet.model_dump_json()
                if self.state.content_type == "tweet"
                else self.state.linkedin_post
            ),
        }))
        self.state.score = result.pydantic

    @router(or_(check_seo, check_virality))
    def score_router(self):
        content_type = self.state.content_type
        score = self.state.score
        print(score)
        if score.score >= 5:
            return "score_passed"
        else:
            if content_type == "blog":
                return "remake_blog"
            elif content_type == "tweet":
                return "remake_tweet"
            return "remake_linkedin_post"

    @listen("score_passed")
    def finalize_content(self):
        """Finalize the content"""
        print("🎉 Finalizing content...")

        if self.state.content_type == "blog":
            print(f"📝 Blog Post: {self.state.blog_post.title}")
            print(f"🔍 SEO Score: {self.state.score.score}/10")
        elif self.state.content_type == "tweet":
            print(f"🐦 Tweet: {self.state.tweet}")
            print(f"🚀 Virality Score: {self.state.score.score}/10")
        elif self.state.content_type == "linkedin":
            print(f"💼 LinkedIn: {self.state.linkedin_post.title}")
            print(f"🚀 Virality Score: {self.state.score.score}/10")

        print("✅ Content ready for publication!")
        return (
            self.state.linkedin_post
            if self.state.content_type == "linkedin"
            else (
                self.state.tweet
                if self.state.content_type == "tweet"
                else self.state.blog_post
            )
        )

    def assign_max_length(self, content_type: Literal["tweet", "blog", "linkedin"]) -> None:
        if content_type == "tweet":
            self.state.max_length = 150
        elif content_type == "blog":
            self.state.max_length = 800
        elif content_type == "linkedin":
            self.state.max_length = 500


flow = ContentPipelineFlow()

flow.kickoff(
    inputs={
        "content_type": "tweet",
        "topic": "AI Dog Training",
    }
)

flow.plot()
