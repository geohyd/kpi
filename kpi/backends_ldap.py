from django_auth_ldap.backend import LDAPBackend


class LDAPKPIBackend(LDAPBackend):
    def authenticate(self, username, password):
        """ Overrides LDAPBackend.authenticate to save user password in django """
        user = LDAPBackend.authenticate(self, None, username, password)
        if user:
            user.extra_details.data['ldap_user'] = True
            user.extra_details.save()
            user.set_password(password)
            user.save()
        #let standard AUTHENTICATION_BACKENDS make the true authentification for binding KPI and KOBOCAT
        #return user

class LDAPBackend1(LDAPKPIBackend):
    settings_prefix = "AUTH_LDAP_1_"

class LDAPBackend2(LDAPKPIBackend):
    settings_prefix = "AUTH_LDAP_2_"

class LDAPBackend3(LDAPKPIBackend):
    settings_prefix = "AUTH_LDAP_3_"