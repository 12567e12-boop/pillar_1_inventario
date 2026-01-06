// Función para manejar el cambio de especialidad
function handleEspecialidadChange(value) {
    // Esta función actualiza el booleano 'herramienta' basado en la selección
    // El campo booleano está oculto pero se actualiza automáticamente
    console.log('Especialidad cambiada a:', value);
}

document.addEventListener('DOMContentLoaded', function() {
    const especialidadSelect = document.getElementById('id_especialidad');
    
    if (!especialidadSelect) {
        console.log('Elemento especialidad no encontrado, reintentando...');
        setTimeout(arguments.callee, 100);
        return;
    }
    
    // No se necesita lógica adicional ya que el campo booleano se maneja
    // automáticamente desde el formulario Django
});
