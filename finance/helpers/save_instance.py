from django.db import transaction
from django.http import Http404

def _pred_origin(request,data,TeamPrediction,operation_team_instance,shared_team_instance, origin_monthly_data, pk: int | None = None):
    """
    origin(dominant) 생성/수정:
      - pk 있으면 UPDATE (id 고정)
      - pk 없으면 CREATE
    """
    # 실적분배 해제면 협업팀 제거
    if getattr(data, "project_category", None) != "Sharing":
        shared_team_instance = None

    with transaction.atomic():
        if pk is not None:
            # -------- UPDATE --------
            try:
                origin_instance = TeamPrediction.objects.select_for_update().get(id=pk)
            except TeamPrediction.DoesNotExist:
                raise Http404(f"ID {pk} 대상이 없습니다.")

            payload = data.model_dump(
                exclude={"operation_team", "shared_team", "monthly_data"},
                exclude_none=True,
            )
            for k, v in payload.items():
                setattr(origin_instance, k, v)

            origin_instance.operation_team = operation_team_instance
            origin_instance.shared_team = shared_team_instance
            origin_instance.owner = request.user
            origin_instance.shared_dominate = True

            # update에서는 monthly_data 그대로 보존
            origin_instance.save()
        else:
            # -------- CREATE --------
            origin_instance = TeamPrediction.objects.create(
                **data.model_dump(
                    exclude={"operation_team", "shared_team", "monthly_data"},
                    exclude_none=True,
                ),
                operation_team=operation_team_instance,
                shared_team=shared_team_instance,
                owner=request.user,
                shared_dominate=True,
                monthly_data=origin_monthly_data or {},  # create 때만
            )

    return origin_instance


def _pred_shared(
    request,
    data,
    TeamPrediction,
    operation_team_instance,
    shared_team_instance,
    shared_monthly_data,
    origin_instance,
    *,
    create_if_missing: bool = True,
):
    if shared_team_instance is None:
        return None

    with transaction.atomic():
        # 🔧 조회 키에서 shared_team 제거 → dominant 1건만 유지
        qs = (TeamPrediction.objects
              .select_for_update()
              .filter(dominant=origin_instance, shared_dominate=False))

        found = list(qs[:2])  # 0/1/2+ 판별
        if len(found) > 1:
            # 이 경우는 데이터가 이미 꼬인 상태 → 운영정책에 맞게 정리(병합/삭제)
            raise Http404("같은 dominant에 종속 레코드가 여러 개입니다. 데이터 정리가 필요합니다.")

        payload = data.model_dump(
            exclude={"operation_team", "shared_team", "monthly_data",
                     "shared_dominate", "dominant", "owner", "id", "pk"},
            exclude_none=True,
        )

        if found:
            # -------- UPDATE --------
            shared_instance = found[0]

            # (보너스 가드) 혹시 dominant로 승격된 레코드를 잘못 잡았는지 확인
            if shared_instance.shared_dominate is True:
                raise Http404("dominant 인스턴스를 shared로 바꿀 수 없습니다.")

            # 일반 필드 반영
            for k, v in payload.items():
                setattr(shared_instance, k, v)

            # 🔧 shared_team을 '새 값'으로 갱신 (이전 A → 새 B로 이동)
            shared_instance.shared_team = shared_team_instance
            shared_instance.operation_team = operation_team_instance
            shared_instance.owner = request.user
            shared_instance.shared_dominate = False
            shared_instance.dominant = origin_instance
            shared_instance.monthly_data = shared_monthly_data

            shared_instance.save()
            return shared_instance

        # -------- NOT FOUND → CREATE --------
        if not create_if_missing:
            raise Http404("해당 dominant의 shared 인스턴스를 찾을 수 없습니다.")

        shared_instance = TeamPrediction.objects.create(
            **payload,
            operation_team=operation_team_instance,
            shared_team=shared_team_instance,
            owner=request.user,
            shared_dominate=False,
            dominant=origin_instance,
            monthly_data=shared_monthly_data,
        )
        return shared_instance
