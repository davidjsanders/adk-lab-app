# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pydantic import BaseModel, Field

class BGPResetSchema(BaseModel):
    device_id: str = Field(
        ..., 
        description="The unique identifier of the target router (e.g., 'tor-01.wat01')."
    )
    peer_ip: str = Field(
        ..., 
        description="The BGP neighbor IP address to reset."
    )
    is_user_confirmed: bool = Field(
        False, 
        description="Flag indicating if the human operator has explicitly typed 'yes' or 'confirm' to execute this."
    )
