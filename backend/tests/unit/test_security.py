from uuid import uuid4
from types import SimpleNamespace
import pytest
from app.core.security import hash_password,verify_password,create_token,decode_token
from app.core.permissions import require_role,district_allowed,check_record
from app.core.exceptions import DomainError,PermissionDenied
from app.core.constants import Role

def test_argon2_passwords_are_salted():
    a=hash_password('correct horse battery');b=hash_password('correct horse battery')
    assert a!=b and a.startswith('$argon2')
    assert verify_password('correct horse battery',a)
    assert not verify_password('wrong',a)

def test_tokens_verify_type_and_signature():
    token,claims=create_token(uuid4(),uuid4())
    assert decode_token(token)['jti']==claims['jti']
    with pytest.raises(DomainError): decode_token(token,'refresh')
    with pytest.raises(DomainError): decode_token(token+'tampered')

def test_role_and_record_scope():
    user=SimpleNamespace(id=uuid4(),role=Role.FARMER,district='Pune')
    with pytest.raises(PermissionDenied): require_role(user,Role.VETERINARIAN)
    with pytest.raises(PermissionDenied): district_allowed(user,'Satara')
    with pytest.raises(PermissionDenied): check_record(SimpleNamespace(owner_id=uuid4(),district='Pune'),user)
    check_record(SimpleNamespace(owner_id=user.id,district='Pune'),user)
