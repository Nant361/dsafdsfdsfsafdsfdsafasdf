import aiohttp
import json
import asyncio
from datetime import datetime
from typing import Tuple, Optional, Dict, List, Any
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def login_pddikti(session: aiohttp.ClientSession) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Login ke PDDikti dan dapatkan token"""
    try:
        logger.info("Starting PDDikti login process...")
        
        # STEP 1: GET /signin untuk mendapatkan cookie
        signin_response = await session.get(
            "https://pddikti-admin.kemdikbud.go.id/signin",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            }
        )
        logger.info(f"Signin response status: {signin_response.status}")
        
        # STEP 2: POST /login/login
        login_data = {
            'data[username]': 'MDQzMTc2',
            'data[password]': 'QEA8PkxrajEyMg==',
            'data[issso]': 'false'
        }
        login_response = await session.post(
            "https://api-pddikti-admin.kemdikbud.go.id/login/login",
            data=login_data,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://pddikti-admin.kemdikbud.go.id",
                "Connection": "keep-alive",
                "Referer": "https://pddikti-admin.kemdikbud.go.id/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site"
            }
        )
        
        logger.info(f"Login response status: {login_response.status}")
        
        if login_response.status == 200:
            data = await login_response.json()
            logger.debug(f"Login response data: {json.dumps(data, indent=2)}")
            
            i_iduser = data["result"]["session_data"]["i_iduser"]
            id_organisasi = data["result"]["session_data"]["i_idunit"]
            
            logger.info(f"Login successful. User ID: {i_iduser}, Org ID: {id_organisasi}")
            
            # STEP 3: GET /isverified
            verify_response = await session.get(
                f"https://api-pddikti-admin.kemdikbud.go.id/isverified/{i_iduser}",
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Referer": "https://pddikti-admin.kemdikbud.go.id/",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site"
                }
            )
            logger.info(f"Verify response status: {verify_response.status}")
            
            # STEP 4: POST /login/roles/1?login=adm
            roles_response = await session.post(
                "https://api-pddikti-admin.kemdikbud.go.id/login/roles/1?login=adm",
                data={'data[i_iduser]': i_iduser},
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://pddikti-admin.kemdikbud.go.id",
                    "Connection": "keep-alive",
                    "Referer": "https://pddikti-admin.kemdikbud.go.id/",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site"
                }
            )
            logger.info(f"Roles response status: {roles_response.status}")
            
            # STEP 5: POST /login/setlogin/3/{id_organisasi}
            setlogin_data = {
                'data[i_username]': '043176',
                'data[i_iduser]': i_iduser,
                'data[password]': '@@<>Lkj122',
                'data[is_manual]': 'true'
            }
            setlogin_response = await session.post(
                f"https://api-pddikti-admin.kemdikbud.go.id/login/setlogin/3/{id_organisasi}?id_pengguna={i_iduser}&id_unit={id_organisasi}&id_role=3",
                data=setlogin_data,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://pddikti-admin.kemdikbud.go.id",
                    "Connection": "keep-alive",
                    "Referer": "https://pddikti-admin.kemdikbud.go.id/",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site"
                }
            )
            
            logger.info(f"Setlogin response status: {setlogin_response.status}")
            
            if setlogin_response.status == 200:
                setlogin_result = await setlogin_response.json()
                logger.debug(f"Setlogin response data: {json.dumps(setlogin_result, indent=2)}")
                
                pm_token = setlogin_result["result"]["session_data"]["pm"]
                logger.info("Login process completed successfully")
                return i_iduser, id_organisasi, pm_token
        
        logger.error("Login failed")
        return None, None, None
                
    except Exception as e:
        logger.error(f"Error during login: {str(e)}", exc_info=True)
        return None, None, None

async def search_student(keyword: str, i_iduser: str, pm_token: str, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Cari data mahasiswa"""
    try:
        logger.info(f"Starting student search with keyword: {keyword}")
        
        # Cari mahasiswa
        search_data = {
            'data[keyword]': keyword,
            'data[id_sp]': '',
            'data[id_sms]': '',
            'data[vld]': '0'
        }
        
        search_url = f"https://api-pddikti-admin.kemdikbud.go.id/mahasiswa/result?limit=20&page=0&id_pengguna={i_iduser}&id_role=3&pm={pm_token}"
        logger.info(f"Search URL: {search_url}")
        logger.debug(f"Search data: {json.dumps(search_data, indent=2)}")
        
        async with session.post(search_url, data=search_data, headers={"User-Agent": "Mozilla/5.0"}) as response:
            logger.info(f"Search response status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                logger.debug(f"Search response data: {json.dumps(data, indent=2)}")
                
                result = data.get("result", {}).get("data", [])
                logger.info(f"Found {len(result)} students")
                return result
            else:
                response_text = await response.text()
                logger.error(f"Search failed with status {response.status}")
                logger.error(f"Response text: {response_text}")
                return []
                
    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        return []

async def get_student_detail(id_reg_pd: str, i_iduser: str, id_organisasi: str, pm_token: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
    """Dapatkan detail mahasiswa"""
    try:
        logger.info(f"Getting student detail for ID: {id_reg_pd}")
        
        # Dapatkan detail mahasiswa
        detail_url = f"https://api-pddikti-admin.kemdikbud.go.id/mahasiswa/detail/{id_reg_pd}?id_pengguna={i_iduser}&id_unit={id_organisasi}&id_role=3&pm={pm_token}"
        logger.info(f"Detail URL: {detail_url}")
        
        async with session.get(detail_url, headers={
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://pddikti-admin.kemdikbud.go.id",
            "Referer": "https://pddikti-admin.kemdikbud.go.id/",
            "Content-Type": "application/json"
        }) as response:
            logger.info(f"Detail response status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                logger.debug(f"Detail response data: {json.dumps(data, indent=2)}")
                
                result = data.get("result", {})
                logger.info("Successfully retrieved student detail")
                return result
            else:
                response_text = await response.text()
                logger.error(f"Get detail failed with status {response.status}")
                logger.error(f"Response text: {response_text}")
                return {}
                
    except Exception as e:
        logger.error(f"Error getting student detail: {str(e)}", exc_info=True)
        return {} 