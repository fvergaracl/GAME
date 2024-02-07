from typing import List, Optional

from pydantic import BaseModel


class BaseRuleSubVariable(BaseModel):
    name: str
    type: str
    description: str


class BaseRuleVariable(BaseModel):
    name: str
    description: str
    sub_variables: Optional[List[BaseRuleSubVariable]]


class ResponseFindAllRuleVariables(BaseModel):
    items: Optional[List[BaseRuleVariable]]
