"""AgentsforBedrockBackend class with methods for supported APIs."""

from typing import Any, Dict, Iterable, List, Optional, Tuple

from moto.bedrockagent.exceptions import (
    ConflictException,
    ResourceNotFoundException,
    ValidationException,
)
from moto.core.base_backend import BackendDict, BaseBackend
from moto.core.common_models import BaseModel
from moto.core.utils import unix_time
from moto.moto_api._internal import mock_random
from moto.utilities.tagging_service import TaggingService


class Agent(BaseModel):
    def __init__(
        self,
        agent_name: str,
        agent_resource_role_arn: str,
        region_name: str,
        account_id: str,
        client_token: Optional[str],
        instruction: Optional[str],
        foundation_model: Optional[str],
        description: Optional[str],
        idle_session_ttl_in_seconds: Optional[int],
        customer_encryption_key_arn: Optional[str],
        prompt_override_configuration: Optional[Dict[str, Any]],
    ):
        self.agent_name = agent_name
        self.client_token = client_token
        self.instruction = instruction
        self.foundation_model = foundation_model
        self.description = description
        self.idle_session_ttl_in_seconds = idle_session_ttl_in_seconds
        self.agent_resource_role_arn = agent_resource_role_arn
        self.customer_encryption_key_arn = customer_encryption_key_arn
        self.prompt_override_configuration = prompt_override_configuration
        self.region_name = region_name
        self.account_id = account_id
        self.created_at = unix_time()
        self.updated_at = unix_time()
        self.prepared_at = unix_time()
        self.agent_status = "PREPARED"
        self.agent_id = self.agent_name + str(mock_random.uuid4())[:8]
        self.agent_arn = f"arn:aws:bedrock:{self.region_name}:{self.account_id}:agent/{self.agent_id}"
        self.agent_version = "1.0"
        self.failure_reasons: List[str] = []
        self.recommended_actions = ["action"]

    def to_dict(self) -> Dict[str, Any]:
        dct = {
            "agentId": self.agent_id,
            "agentName": self.agent_name,
            "agentArn": self.agent_arn,
            "agentVersion": self.agent_version,
            "clientToken": self.client_token,
            "instruction": self.instruction,
            "agentStatus": self.agent_status,
            "foundationModel": self.foundation_model,
            "description": self.description,
            "idleSessionTTLInSeconds": self.idle_session_ttl_in_seconds,
            "agentResourceRoleArn": self.agent_resource_role_arn,
            "customerEncryptionKeyArn": self.customer_encryption_key_arn,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "preparedAt": self.prepared_at,
            "failureReasons": self.failure_reasons,
            "recommendedActions": self.recommended_actions,
            "promptOverrideConfiguration": self.prompt_override_configuration,
        }
        return {k: v for k, v in dct.items() if v}

    def dict_summary(self) -> Dict[str, Any]:
        dct = {
            "agentId": self.agent_id,
            "agentName": self.agent_name,
            "agentStatus": self.agent_status,
            "description": self.description,
            "updatedAt": self.updated_at,
            "latestAgentVersion": self.agent_version,
        }
        return {k: v for k, v in dct.items() if v}


class KnowledgeBase(BaseModel):
    def __init__(
        self,
        name: str,
        role_arn: str,
        region_name: str,
        account_id: str,
        knowledge_base_configuration: Dict[str, Any],
        storage_configuration: Dict[str, Any],
        client_token: Optional[str],
        description: Optional[str],
    ):
        self.client_token = client_token
        self.name = name
        self.description = description
        self.role_arn = role_arn
        if knowledge_base_configuration["type"] != "VECTOR":
            raise ValidationException(
                "Validation error detected: "
                f"Value '{knowledge_base_configuration['type']}' at 'knowledgeBaseConfiguration' failed to satisfy constraint: "
                "Member must contain 'type' as 'VECTOR'"
            )
        self.knowledge_base_configuration = knowledge_base_configuration
        if storage_configuration["type"] not in [
            "OPENSEARCH_SERVERLESS",
            "PINECONE",
            "REDIS_ENTERPRISE_CLOUD",
            "RDS",
        ]:
            raise ValidationException(
                "Validation error detected: "
                f"Value '{storage_configuration['type']}' at 'storageConfiguration' failed to satisfy constraint: "
                "Member 'type' must be one of: OPENSEARCH_SERVERLESS | PINECONE | REDIS_ENTERPRISE_CLOUD | RDS"
            )
        self.storage_configuration = storage_configuration
        self.region_name = region_name
        self.account_id = account_id
        self.knowledge_base_id = self.name + str(mock_random.uuid4())[:8]
        self.knowledge_base_arn = f"arn:aws:bedrock:{self.region_name}:{self.account_id}:knowledge-base/{self.knowledge_base_id}"
        self.created_at = unix_time()
        self.updated_at = unix_time()
        self.status = "Active"
        self.failure_reasons: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        dct = {
            "knowledgeBaseId": self.knowledge_base_id,
            "name": self.name,
            "knowledgeBaseArn": self.knowledge_base_arn,
            "description": self.description,
            "roleArn": self.role_arn,
            "knowledgeBaseConfiguration": self.knowledge_base_configuration,
            "storageConfiguration": self.storage_configuration,
            "status": self.status,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "failureReasons": self.failure_reasons,
        }
        return {k: v for k, v in dct.items() if v}

    def dict_summary(self) -> Dict[str, Any]:
        dct = {
            "knowledgeBaseId": self.knowledge_base_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "updatedAt": self.updated_at,
        }
        return {k: v for k, v in dct.items() if v}


class AgentsforBedrockBackend(BaseBackend):
    """Implementation of AgentsforBedrock APIs."""

    def __init__(self, region_name: str, account_id: str):
        super().__init__(region_name, account_id)
        self.Agents: Dict[str, Agent] = {}
        self.KnowledgeBases: Dict[str, KnowledgeBase] = {}
        self.tagger = TaggingService()

    def _list_arns(self) -> List[str]:
        return [agent.agent_arn for agent in self.Agents.values()] + [
            knowledge_base.knowledge_base_arn
            for knowledge_base in self.KnowledgeBases.values()
        ]

    def create_agent(
        self,
        agent_name: str,
        agent_resource_role_arn: str,
        client_token: Optional[str],
        instruction: Optional[str],
        foundation_model: Optional[str],
        description: Optional[str],
        idle_session_ttl_in_seconds: Optional[int],
        customer_encryption_key_arn: Optional[str],
        tags: Optional[Dict[str, str]],
        prompt_override_configuration: Optional[Dict[str, Any]],
    ) -> Agent:
        agent = Agent(
            agent_name,
            agent_resource_role_arn,
            self.region_name,
            self.account_id,
            client_token,
            instruction,
            foundation_model,
            description,
            idle_session_ttl_in_seconds,
            customer_encryption_key_arn,
            prompt_override_configuration,
        )
        self.Agents[agent.agent_id] = agent
        if tags:
            self.tag_resource(agent.agent_arn, tags)
        return agent

    def get_agent(self, agent_id: str) -> Agent:
        if agent_id not in self.Agents:
            raise ResourceNotFoundException(f"Agent {agent_id} not found")
        return self.Agents[agent_id]

    def list_agents(
        self, max_results: Optional[int], next_token: Optional[str]
    ) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        if next_token:
            try:
                starting_index = int(next_token)
                if starting_index > len(self.Agents):
                    raise ValueError  # invalid next_token
            except ValueError:
                raise ValidationException('Invalid pagination token because "{0}".')
        else:
            starting_index = 0

        if max_results:
            end_index = max_results + starting_index
            agents_fetched: Iterable[Agent] = list(self.Agents.values())[
                starting_index:end_index
            ]
            if end_index >= len(self.Agents):
                next_index = None
            else:
                next_index = end_index
        else:
            agents_fetched = list(self.Agents.values())[starting_index:]
            next_index = None

        agent_summaries = [agent.dict_summary() for agent in agents_fetched]

        index = str(next_index) if next_index is not None else None
        return index, agent_summaries

    def delete_agent(
        self, agent_id: str, skip_resource_in_use_check: Optional[bool]
    ) -> Tuple[str, str]:
        if agent_id in self.Agents:
            if (
                skip_resource_in_use_check
                or self.Agents[agent_id].agent_status == "PREPARED"
            ):
                self.Agents[agent_id].agent_status = "DELETING"
                agent_status = self.Agents[agent_id].agent_status
                del self.Agents[agent_id]
            else:
                raise ConflictException(f"Agent {agent_id} is in use")
        else:
            raise ResourceNotFoundException(f"Agent {agent_id} not found")
        return agent_id, agent_status

    def create_knowledge_base(
        self,
        name: str,
        role_arn: str,
        knowledge_base_configuration: Dict[str, Any],
        storage_configuration: Dict[str, Any],
        client_token: Optional[str],
        description: Optional[str],
        tags: Optional[Dict[str, str]],
    ) -> KnowledgeBase:
        knowledge_base = KnowledgeBase(
            name,
            role_arn,
            self.region_name,
            self.account_id,
            knowledge_base_configuration,
            storage_configuration,
            client_token,
            description,
        )
        self.KnowledgeBases[knowledge_base.knowledge_base_id] = knowledge_base
        if tags:
            self.tag_resource(knowledge_base.knowledge_base_arn, tags)
        return knowledge_base

    def list_knowledge_bases(
        self, max_results: Optional[int], next_token: Optional[str]
    ) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        if next_token:
            try:
                starting_index = int(next_token)
                if starting_index > len(self.KnowledgeBases):
                    raise ValueError  # invalid next_token
            except ValueError:
                raise ValidationException('Invalid pagination token because "{0}".')
        else:
            starting_index = 0

        if max_results:
            end_index = max_results + starting_index
            knowledge_bases_fetched: Iterable[KnowledgeBase] = list(
                self.KnowledgeBases.values()
            )[starting_index:end_index]
            if end_index >= len(self.KnowledgeBases):
                next_index = None
            else:
                next_index = end_index
        else:
            knowledge_bases_fetched = list(self.KnowledgeBases.values())[
                starting_index:
            ]
            next_index = None

        knowledge_base_summaries = [
            knowledge_base.dict_summary() for knowledge_base in knowledge_bases_fetched
        ]

        index = str(next_index) if next_index is not None else None
        return index, knowledge_base_summaries

    def delete_knowledge_base(self, knowledge_base_id: str) -> Tuple[str, str]:
        if knowledge_base_id in self.KnowledgeBases:
            self.KnowledgeBases[knowledge_base_id].status = "DELETING"
            knowledge_base_status = self.KnowledgeBases[knowledge_base_id].status
            del self.KnowledgeBases[knowledge_base_id]
        else:
            raise ResourceNotFoundException(
                f"Knowledge base {knowledge_base_id} not found"
            )
        return knowledge_base_id, knowledge_base_status

    def get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBase:
        if knowledge_base_id not in self.KnowledgeBases:
            raise ResourceNotFoundException(
                f"Knowledge base {knowledge_base_id} not found"
            )
        return self.KnowledgeBases[knowledge_base_id]

    def tag_resource(self, resource_arn: str, tags: Dict[str, str]) -> None:
        if resource_arn not in self._list_arns():
            raise ResourceNotFoundException(f"Resource {resource_arn} not found")
        tags_input = TaggingService.convert_dict_to_tags_input(tags or {})
        self.tagger.tag_resource(resource_arn, tags_input)
        return

    def untag_resource(self, resource_arn: str, tag_keys: List[str]) -> None:
        if resource_arn not in self._list_arns():
            raise ResourceNotFoundException(f"Resource {resource_arn} not found")
        self.tagger.untag_resource_using_names(resource_arn, tag_keys)
        return

    def list_tags_for_resource(self, resource_arn: str) -> Dict[str, str]:
        if resource_arn not in self._list_arns():
            raise ResourceNotFoundException(f"Resource {resource_arn} not found")
        return self.tagger.get_tag_dict_for_resource(resource_arn)


bedrockagent_backends = BackendDict(AgentsforBedrockBackend, "bedrock")
