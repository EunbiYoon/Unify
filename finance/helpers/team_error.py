from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

def _pred_team(data, Team, shared_dominate): 
    operation_team_str = getattr(data, "operation_team", None)
    shared_team_str = getattr(data, "shared_team", None)
    
    # 1) 운영팀 꼭 존재해야함 아니면 에러
    if not operation_team_str:
        raise HttpError(400, "❌ operation_team은 필수입니다.")
    operation_team_instance = get_object_or_404(Team, team_name = operation_team_str)

    # 5) shared_dominate=False인 애들은 절대 수정 불가
    if shared_dominate==False:
        raise HttpError(400, "❌ 의존 프로젝트는 수정이 불가합니다.")

    if shared_team_str:
        # 2) 협업팀 몾찾으면 에러 
        shared_team_instance = get_object_or_404(Team, team_name = shared_team_str)
        
        # 3) project_category가 Sharing이 아니면 shared_team 을 가질수 없다
        if data.project_category != "Sharing":
            raise HttpError(400, "실적분배 프로젝트가 아님으로 협업팀을 가질 수 없습니다.")

        # 4) 협업팀과 운영팀은 절대 같을 수 없다
        if operation_team_instance.id == shared_team_instance.id:
            raise HttpError(400, "운영팀과 협업팀은 같을 수 없습니다.")
    
    else:
        shared_team_instance=shared_team_str

    return operation_team_instance, shared_team_instance
