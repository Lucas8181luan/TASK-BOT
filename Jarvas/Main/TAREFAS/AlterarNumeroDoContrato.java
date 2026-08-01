package TAREFAS;
import java.awt.AWTException;
import java.awt.Robot;
import java.awt.event.KeyEvent;

public class AlterarNumeroDoContrato {
    
    private static Robot robot;
    
    static {
        try {
            robot = new Robot();
        } catch (AWTException e) {
            System.err.println("Erro ao inicializar o Robot: " + e.getMessage());
        }
    }
    
    /** Função principal para mudar número de contrato */
    public static void executarMudarContrato() {
        try {
            timeSleep(5000);

            int c = 0;

            for (int i = 0; i < 3000; i++) {
                c++ ;
                pressKey(KeyEvent.VK_DOWN);
                timeSleep(1000);
                
                pressKey(KeyEvent.VK_ENTER);
                timeSleep(1000);
                
                int valorAtual = 5917;
                int numero = valorAtual + c;
                String matricula = String.valueOf(numero);
                
                for (int j = 0; j < 4; j++) {
                    pressKey(KeyEvent.VK_BACK_SPACE);
                }
                timeSleep(1000);
                
                writeText(matricula);
                timeSleep(1000);
                
                for (int k = 0; k < 29; k++) {
                    pressKey(KeyEvent.VK_TAB);
                }
                
                pressKey(KeyEvent.VK_ENTER);
                timeSleep(1000);
            }
            
        } catch (Exception e) {
            System.err.println("Erro na execução do bot: " + e.getMessage());
        }
    }
    
    // Métodos auxiliares
    private static void timeSleep(int milliseconds) {
        try {
            Thread.sleep(milliseconds);
        } catch (InterruptedException e) {
            System.err.println("Thread interrompida: " + e.getMessage());
        }
    }
    
    private static void pressKey(int keyCode) {
        robot.keyPress(keyCode);
        robot.keyRelease(keyCode);
    }
    
    private static void writeText(String text) {
        // Simula a digitação do texto caractere por caractere
        for (char c : text.toCharArray()) {
            int keyCode = getKeyCodeForChar(c);
            if (keyCode != -1) {
                pressKey(keyCode);
            }
        }
    }
    
    private static int getKeyCodeForChar(char c) {
        // Mapeia caracteres para KeyEvent (apenas números para este caso)
        switch (c) {
            case '0': return KeyEvent.VK_0;
            case '1': return KeyEvent.VK_1;
            case '2': return KeyEvent.VK_2;
            case '3': return KeyEvent.VK_3;
            case '4': return KeyEvent.VK_4;
            case '5': return KeyEvent.VK_5;
            case '6': return KeyEvent.VK_6;
            case '7': return KeyEvent.VK_7;
            case '8': return KeyEvent.VK_8;
            case '9': return KeyEvent.VK_9;
            default: return -1;
        }
    }
    
    // Executar apenas se chamado diretamente
    public static void main(String[] args) {
        executarMudarContrato();
    }
}