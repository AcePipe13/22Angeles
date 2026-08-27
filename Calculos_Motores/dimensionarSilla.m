function R = dimensionarSilla(P)

%==========================================================================
% DIMENSIONAMIENTO DE SILLA DE RUEDAS ELECTRICA
%
% Evalua:
%   - Fuerzas
%   - Torque requerido
%   - Potencia requerida
%   - RPM de rueda
%   - Relacion de reduccion
%   - Motor comercial seleccionado
%
%==========================================================================


%% ========================================================================
% 1. CONSTANTES
% ========================================================================

g = 9.81;


%% ========================================================================
% 2. ENTRADAS
% ========================================================================

m_total          = P.m_total;
num_motores      = P.num_motores;

r_rueda          = P.r_rueda;

eta_motor        = P.eta_motor;
eta_reductor     = P.eta_reductor;
eta_transmision  = P.eta_transmision;

Crr              = P.Crr;

v_max_kmh        = P.v_max_kmh;
a                = P.a;

pendiente_deg    = P.pendiente_deg;

factor_seguridad = P.factor_seguridad;

rho_aire         = P.rho_aire;
Cd               = P.Cd;
A_frontal        = P.A_frontal;

V_motor          = P.V_motor;
P_motor_nominal  = P.P_motor_nominal;

RPM_motor_interno     = P.RPM_motor_interno;
RPM_salida_reductor   = P.RPM_salida_reductor;


%% ========================================================================
% 3. CONVERSIONES
% ========================================================================

v_max = v_max_kmh / 3.6;

theta = deg2rad(pendiente_deg);

eta_total = ...
    eta_motor * eta_reductor * eta_transmision;


%% ========================================================================
% 4. FUERZAS DEL SISTEMA
% ========================================================================

F_rod_total = ...
    Crr * m_total * g * cos(theta);

F_pendiente_total = ...
    m_total * g * sin(theta);

F_inercia_total = ...
    m_total * a;

F_aero_total = ...
    0.5 * rho_aire * Cd * A_frontal * v_max^2;

F_total = ...
    F_rod_total + ...
    F_pendiente_total + ...
    F_inercia_total + ...
    F_aero_total;


%% ========================================================================
% 5. FUERZA POR MOTOR
% ========================================================================

F_motor = ...
    F_total / num_motores;


%% ========================================================================
% 6. TORQUE REQUERIDO EN RUEDA
% ========================================================================

T_rueda_motor = ...
    F_motor * r_rueda;


%% ========================================================================
% 7. TORQUE REQUERIDO CON PERDIDAS
% ========================================================================

T_salida_minima = ...
    T_rueda_motor / eta_total;


%% ========================================================================
% 8. TORQUE RECOMENDADO
% ========================================================================

T_salida_recomendada = ...
    T_salida_minima * factor_seguridad;


%% ========================================================================
% 9. RPM NECESARIAS EN LA RUEDA
% ========================================================================

omega_rueda = ...
    v_max / r_rueda;

RPM_rueda = ...
    omega_rueda * 60 / (2*pi);


%% ========================================================================
% 10. RELACION DE REDUCCION NECESARIA
% ========================================================================

relacion_reduccion_necesaria = ...
    RPM_motor_interno / RPM_rueda;


%% ========================================================================
% 11. RELACION DE REDUCCION REAL DEL MOTOR SELECCIONADO
% ========================================================================

relacion_reduccion_motor = ...
    RPM_motor_interno / RPM_salida_reductor;


%% ========================================================================
% 12. VELOCIDAD REAL CON EL MOTOR SELECCIONADO
% ========================================================================

circunferencia_rueda = ...
    2*pi*r_rueda;

velocidad_real_ms = ...
    (RPM_salida_reductor/60) * circunferencia_rueda;

velocidad_real_kmh = ...
    velocidad_real_ms * 3.6;


%% ========================================================================
% 13. POTENCIA REQUERIDA
% ========================================================================

P_mecanica_total = ...
    F_total * v_max;

P_mecanica_motor = ...
    P_mecanica_total / num_motores;

P_electrica_motor = ...
    P_mecanica_motor / eta_total;

P_motor_recomendado = ...
    P_electrica_motor * factor_seguridad;

P_electrica_total = ...
    P_electrica_motor * num_motores;

P_recomendada_total = ...
    P_motor_recomendado * num_motores;


%% ========================================================================
% 14. TORQUE TEORICO DEL MOTOR COMERCIAL A 120 RPM
% ========================================================================

omega_salida_reductor = ...
    RPM_salida_reductor * 2*pi/60;

T_motor_comercial_ideal = ...
    P_motor_nominal / omega_salida_reductor;


%% ========================================================================
% 15. TORQUE ESTIMADO REAL
%
% Si los 350 W publicados fueran potencia electrica de entrada,
% estimamos la potencia mecanica real usando eficiencia motor+reductor.
% ========================================================================

eta_motorreductor = ...
    eta_motor * eta_reductor;

P_salida_estimada = ...
    P_motor_nominal * eta_motorreductor;

T_motor_comercial_estimado = ...
    P_salida_estimada / omega_salida_reductor;


%% ========================================================================
% 16. CORRIENTE
% ========================================================================

I_nominal_estimada = ...
    P_motor_nominal / V_motor;

I_requerida_motor = ...
    P_electrica_motor / V_motor;

I_recomendada_motor = ...
    P_motor_recomendado / V_motor;


%% ========================================================================
% 17. COMPARACION DE POTENCIA
% ========================================================================

if P_motor_nominal >= P_motor_recomendado

    estado_potencia = 'CUMPLE CON FACTOR DE SEGURIDAD';

elseif P_motor_nominal >= P_electrica_motor

    estado_potencia = ...
        'CUMPLE MINIMO, PERO SIN FACTOR DE SEGURIDAD COMPLETO';

else

    estado_potencia = 'NO CUMPLE';

end


%% ========================================================================
% 18. COMPARACION DE TORQUE
% ========================================================================

if T_motor_comercial_estimado >= T_salida_recomendada

    estado_torque = 'CUMPLE CON FACTOR DE SEGURIDAD';

elseif T_motor_comercial_estimado >= T_salida_minima

    estado_torque = ...
        'CUMPLE MINIMO, PERO SIN FACTOR DE SEGURIDAD COMPLETO';

else

    estado_torque = 'NO CUMPLE';

end


%% ========================================================================
% 19. RESULTADOS
% ========================================================================

R = struct();


%% SISTEMA

R.sistema.masa_total_kg = m_total;
R.sistema.numero_motores = num_motores;
R.sistema.radio_rueda_m = r_rueda;
R.sistema.diametro_rueda_m = 2*r_rueda;
R.sistema.velocidad_objetivo_kmh = v_max_kmh;
R.sistema.pendiente_grados = pendiente_deg;
R.sistema.factor_seguridad = factor_seguridad;


%% EFICIENCIA

R.eficiencia.motor = eta_motor;
R.eficiencia.reductor = eta_reductor;
R.eficiencia.transmision = eta_transmision;
R.eficiencia.total = eta_total;


%% FUERZA

R.fuerza.total_N = F_total;
R.fuerza.por_motor_N = F_motor;


%% TORQUE

R.torque.rueda_por_motor_Nm = ...
    T_rueda_motor;

R.torque.salida_minima_Nm = ...
    T_salida_minima;

R.torque.salida_recomendada_Nm = ...
    T_salida_recomendada;

R.torque.motor_comercial_ideal_Nm = ...
    T_motor_comercial_ideal;

R.torque.motor_comercial_estimado_Nm = ...
    T_motor_comercial_estimado;


%% POTENCIA

R.potencia.mecanica_por_motor_W = ...
    P_mecanica_motor;

R.potencia.electrica_por_motor_W = ...
    P_electrica_motor;

R.potencia.recomendada_por_motor_W = ...
    P_motor_recomendado;


%% VELOCIDAD

R.velocidad.RPM_rueda_requerida = ...
    RPM_rueda;

R.velocidad.RPM_salida_motor = ...
    RPM_salida_reductor;

R.velocidad.real_kmh = ...
    velocidad_real_kmh;


%% REDUCCION

R.reduccion.necesaria = ...
    relacion_reduccion_necesaria;

R.reduccion.motor_real = ...
    relacion_reduccion_motor;


%% MOTOR

R.motor.voltaje_V = V_motor;
R.motor.potencia_nominal_W = P_motor_nominal;
R.motor.RPM_interno = RPM_motor_interno;
R.motor.RPM_salida = RPM_salida_reductor;
R.motor.corriente_nominal_estimada_A = ...
    I_nominal_estimada;


%% ESTADOS

R.estado.potencia = estado_potencia;
R.estado.torque = estado_torque;


%% ========================================================================
% 20. MOSTRAR RESULTADOS
% ========================================================================

fprintf('\n');
fprintf('====================================================================\n');
fprintf('         DIMENSIONAMIENTO SILLA + MOTOR MY1016Z-W\n');
fprintf('====================================================================\n');


fprintf('\nDATOS DEL SISTEMA\n');
fprintf('--------------------------------------------------------------------\n');

fprintf('Masa total:                  %.2f kg\n', ...
    m_total);

fprintf('Numero de motores:           %d\n', ...
    num_motores);

fprintf('Diametro rueda:              %.1f cm\n', ...
    2*r_rueda*100);

fprintf('Velocidad objetivo:          %.2f km/h\n', ...
    v_max_kmh);

fprintf('Pendiente:                   %.2f grados\n', ...
    pendiente_deg);

fprintf('Eficiencia total:            %.3f\n', ...
    eta_total);


fprintf('\nFUERZAS\n');
fprintf('--------------------------------------------------------------------\n');

fprintf('Fuerza total sistema:        %.2f N\n', ...
    F_total);

fprintf('Fuerza por motor:            %.2f N\n', ...
    F_motor);


fprintf('\nTORQUE REQUERIDO POR MOTOR\n');
fprintf('--------------------------------------------------------------------\n');

fprintf('Torque directo en rueda:     %.2f N.m\n', ...
    T_rueda_motor);

fprintf('Torque minimo con perdidas:  %.2f N.m\n', ...
    T_salida_minima);

fprintf('Torque recomendado FS=%.2f:   %.2f N.m\n', ...
    factor_seguridad, ...
    T_salida_recomendada);


fprintf('\nMOTOR SELECCIONADO MY1016Z-W\n');
fprintf('--------------------------------------------------------------------\n');

fprintf('Voltaje:                     %.0f V\n', ...
    V_motor);

fprintf('Potencia nominal:            %.0f W\n', ...
    P_motor_nominal);

fprintf('RPM internas:                %.0f rpm\n', ...
    RPM_motor_interno);

fprintf('RPM salida reductora:        %.0f rpm\n', ...
    RPM_salida_reductor);

fprintf('Relacion reductora real:     %.2f : 1\n', ...
    relacion_reduccion_motor);

fprintf('Torque teorico ideal:        %.2f N.m\n', ...
    T_motor_comercial_ideal);

fprintf('Torque estimado real:        %.2f N.m\n', ...
    T_motor_comercial_estimado);


fprintf('\nVELOCIDAD\n');
fprintf('--------------------------------------------------------------------\n');

fprintf('RPM necesarias en rueda:     %.2f rpm\n', ...
    RPM_rueda);

fprintf('RPM disponibles:             %.2f rpm\n', ...
    RPM_salida_reductor);

fprintf('Velocidad objetivo:          %.2f km/h\n', ...
    v_max_kmh);

fprintf('Velocidad real a 120 rpm:    %.2f km/h\n', ...
    velocidad_real_kmh);


fprintf('\nREDUCCION\n');
fprintf('--------------------------------------------------------------------\n');

fprintf('Reduccion teorica necesaria: %.2f : 1\n', ...
    relacion_reduccion_necesaria);

fprintf('Reduccion real motor:        %.2f : 1\n', ...
    relacion_reduccion_motor);


fprintf('\nPOTENCIA POR MOTOR\n');
fprintf('--------------------------------------------------------------------\n');

fprintf('Potencia mecanica requerida: %.2f W\n', ...
    P_mecanica_motor);

fprintf('Potencia electrica minima:   %.2f W\n', ...
    P_electrica_motor);

fprintf('Potencia recomendada:        %.2f W\n', ...
    P_motor_recomendado);

fprintf('Potencia motor seleccionado: %.2f W\n', ...
    P_motor_nominal);


fprintf('\nCORRIENTE\n');
fprintf('--------------------------------------------------------------------\n');

fprintf('Corriente nominal motor:     %.2f A\n', ...
    I_nominal_estimada);

fprintf('Corriente minima requerida:  %.2f A\n', ...
    I_requerida_motor);

fprintf('Corriente recomendada:       %.2f A\n', ...
    I_recomendada_motor);


fprintf('\n====================================================================\n');
fprintf('                 EVALUACION DEL MOTOR\n');
fprintf('====================================================================\n');

fprintf('\nPOTENCIA:\n');
fprintf('   %s\n', estado_potencia);

fprintf('\nTORQUE:\n');
fprintf('   %s\n', estado_torque);


fprintf('\n');

if ...
    P_motor_nominal >= P_electrica_motor && ...
    T_motor_comercial_estimado >= T_salida_minima

    fprintf('RESULTADO GENERAL:\n');
    fprintf('   EL MOTOR PUEDE MOVER EL SISTEMA EN LA CONDICION NOMINAL.\n');

    if ...
        P_motor_nominal < P_motor_recomendado || ...
        T_motor_comercial_estimado < T_salida_recomendada

        fprintf('   PERO NO CUMPLE COMPLETAMENTE EL FACTOR DE SEGURIDAD.\n');

    end

else

    fprintf('RESULTADO GENERAL:\n');
    fprintf('   EL MOTOR NO ES ADECUADO PARA ESTA CONDICION DE DISENO.\n');

end


fprintf('\n');
fprintf('====================================================================\n');

end