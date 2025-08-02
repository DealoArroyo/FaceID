import React, { useState, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

export default function App() {
  const cameraRef = useRef(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [loading, setLoading] = useState(false);

  const takePicture = async () => {
    if (cameraRef.current) {
      setLoading(true);
      try {
        const photo = await cameraRef.current.takePictureAsync({ base64: false });
  
        const formData = new FormData();
        formData.append('file', {
          uri: photo.uri,
          name: 'photo.jpg',
          type: 'image/jpeg',
        });
  
        const response = await fetch('http://192.168.0.36:8000/verify-face/', {
          method: 'POST',
          body: formData,
        });

        // Asegúrate de que la respuesta sea exitosa antes de parsear el JSON
        if (!response.ok) {
          throw new Error(`Error del servidor: ${response.status}`);
        }
  
        const result = await response.json();

        // Usa Alert para mostrar mensajes de forma más clara
        if (result.access === 'granted') {
          Alert.alert(
            '✅ Acceso permitido',
            `Distancia: ${result.min_distance?.toFixed(3) ?? 'N/A'}`
          );
        } else {
          Alert.alert(
            '❌ Acceso denegado',
            `Distancia: ${result.min_distance?.toFixed(3) ?? 'N/A'}\nMotivo: ${result.reason || 'Desconocido'}`
          );
        }

      } catch (e) {
        console.error('Error al tomar o enviar la foto:', e);
        Alert.alert('⚠️ Error', 'Hubo un problema al procesar la foto.');
      } finally {
        setLoading(false);
      }
    }
  };
  
  if (!permission) {
    return <View style={styles.container}><Text style={styles.permissionText}>Cargando permisos...</Text></View>;
  }

  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.permissionText}>Necesitamos tu permiso para acceder a la cámara</Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.buttonText}>Otorgar permiso</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={styles.camera}
        facing={'front'}
      />
      <TouchableOpacity style={styles.button} onPress={takePicture}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>📸 Tomar foto</Text>}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'center',
    alignItems: 'center',
  },
  camera: {
    flex: 1,
    width: '100%',
  },
  button: {
    position: 'absolute',
    bottom: 40,
    left: '25%',
    right: '25%',
    backgroundColor: '#6200ee',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
  },
  permissionText: {
    color: '#fff',
    textAlign: 'center',
    marginBottom: 20,
    fontSize: 18,
  },
  permissionButton: {
    backgroundColor: '#1e88e5',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  }
});